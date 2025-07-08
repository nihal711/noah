from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models import User, LeaveRequest, LeaveBalance, OvertimeRequest, OvertimeLeave
from schemas import LeaveRequestCreate, LeaveRequestResponse, LeaveRequestUpdate, LeaveBalanceResponse, MessageResponse, LeaveRequestWithEmployeeResponse
from auth import get_current_active_user
from utils import verify_manager_permission, is_manager
from datetime import datetime, timedelta
from sqlalchemy import extract
from sqlalchemy.sql import func
from api_utils.leave import is_leave_type_eligible

router = APIRouter(prefix="/leave", tags=["Leave Management"])

# Allowed leave types and their default balances
ALLOWED_LEAVE_TYPES = ["Annual", "Sick", "Casual", "Maternity", "Paternity", "Hajj"]
DEFAULT_LEAVE_BALANCES = {
    "Annual": 25.0,
    "Sick": 10.0,
    "Casual": 5.0,
    "Maternity": 90.0,
    "Paternity": 10.0,
    "Hajj": 30.0
}

def validate_leave_type(leave_type: str, user=None):
    if leave_type not in ALLOWED_LEAVE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid leave type '{leave_type}'. Allowed types: {', '.join(ALLOWED_LEAVE_TYPES)}"
        )
    # Eligibility checks
    if user:
        if leave_type == "Maternity" and user.gender.lower() != "female":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maternity leave is only available for female employees."
            )
        if leave_type == "Paternity" and user.gender.lower() != "male":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Paternity leave is only available for male employees."
            )
        if leave_type == "Hajj" and user.religion.strip().lower() != "muslim":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hajj leave is only available for Muslim employees."
            )

def check_leave_balance(db: Session, user_id: int, leave_type: str, days_requested: float) -> None:
    """
    Check if user has sufficient leave balance.
    Raises HTTPException if balance is insufficient.
    """
    current_year = datetime.now().year
    leave_balance = db.query(LeaveBalance).filter(
        LeaveBalance.user_id == user_id,
        LeaveBalance.leave_type == leave_type,
        LeaveBalance.year == current_year
    ).first()
    
    if not leave_balance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No leave balance found for {leave_type} leave in {current_year}"
        )
    
    if leave_balance.remaining_days < days_requested:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient {leave_type} leave balance. You have {leave_balance.remaining_days} days remaining, but requested {days_requested} days"
        )

def update_leave_balance(db: Session, user_id: int, leave_type: str, days_requested: float) -> None:
    """
    Update leave balance by deducting the requested days.
    """
    current_year = datetime.now().year
    leave_balance = db.query(LeaveBalance).filter(
        LeaveBalance.user_id == user_id,
        LeaveBalance.leave_type == leave_type,
        LeaveBalance.year == current_year
    ).first()
    
    if not leave_balance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No leave balance found for {leave_type} leave in {current_year}"
        )
    
    leave_balance.used_days += days_requested
    leave_balance.remaining_days -= days_requested
    
    if leave_balance.remaining_days < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve leave request. It would result in negative balance for {leave_type} leave"
        )

def has_overlapping_leave(db: Session, user_id: int, start_date, end_date) -> bool:
    overlapping = db.query(LeaveRequest).filter(
        LeaveRequest.user_id == user_id,
        LeaveRequest.status.in_(["pending", "approved"]),
        LeaveRequest.start_date <= end_date,
        LeaveRequest.end_date >= start_date
    ).first()
    return overlapping is not None

# Leave Request Endpoints
@router.post("/requests", response_model=LeaveRequestResponse, summary="Apply for Leave", description="Submit a new leave request. Allowed leave types: Annual, Sick, Casual, Maternity, Paternity, Hajj.")
async def apply_leave(
    leave_request: LeaveRequestCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    validate_leave_type(leave_request.leave_type, user=current_user)
    check_leave_balance(db, current_user.id, leave_request.leave_type, leave_request.days_requested)
    # Check for overlapping leave requests
    if has_overlapping_leave(db, current_user.id, leave_request.start_date, leave_request.end_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a leave request (pending or approved) that overlaps with the requested dates."
        )
    db_leave_request = LeaveRequest(
        user_id=current_user.id,
        leave_type=leave_request.leave_type,
        start_date=leave_request.start_date,
        end_date=leave_request.end_date,
        days_requested=leave_request.days_requested,
        reason=leave_request.reason
    )
    db.add(db_leave_request)
    db.commit()
    db.refresh(db_leave_request)
    return db_leave_request

@router.get("/requests", response_model=List[LeaveRequestResponse], summary="Get My Leave Requests", description="Retrieve all leave requests for current user")
async def get_my_leave_requests(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    leave_requests = db.query(LeaveRequest).filter(LeaveRequest.user_id == current_user.id).all()
    return leave_requests

@router.get("/requests/all", response_model=List[LeaveRequestResponse], summary="Get All Leave Requests", description="Retrieve all leave requests (manager/HR function)")
async def get_all_leave_requests(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):

    if not is_manager(db, current_user):
        raise HTTPException(status_code=403, detail="Only managers can view all leave requests.")
    leave_requests = db.query(LeaveRequest).offset(skip).limit(limit).all()
    return leave_requests

@router.get(
    "/requests/pending-approval",
    response_model=List[LeaveRequestWithEmployeeResponse],
    summary="Get Pending Leave Requests for Manager Approval",
    description="Retrieve all pending leave requests for subordinates of the current manager"
)
async def get_pending_requests_for_manager_approval(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if not is_manager(db, current_user):
        raise HTTPException(status_code=403, detail="Only managers can view pending leave requests for approval.")

    subordinates = db.query(User).filter(User.manager_id == current_user.id).all()
    if not subordinates:
        return []

    subordinate_ids = [s.id for s in subordinates]

    leave_requests = (
        db.query(LeaveRequest)
        .options(joinedload(LeaveRequest.user))
        .filter(
            LeaveRequest.user_id.in_(subordinate_ids),
            LeaveRequest.status == "pending"
        )
        .all()
    )

    result = []
    for req in leave_requests:
        result.append(
            LeaveRequestWithEmployeeResponse(
                id=req.id,
                user_id=req.user_id,
                leave_type=req.leave_type,
                start_date=req.start_date,
                end_date=req.end_date,
                days_requested=req.days_requested,
                reason=req.reason,
                status=req.status,
                approver_comments=req.approver_comments,
                created_at=req.created_at,
                updated_at=req.updated_at,
                employee_name=req.user.username if req.user else None,
                employee_email=req.user.email if req.user else None,
            )
        )
    return result

@router.get("/requests/{request_id}", response_model=LeaveRequestResponse, summary="Get Leave Request by ID", description="Retrieve a specific leave request by ID")
async def get_leave_request(
    request_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    if leave_request is None:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    # Users can only see their own requests unless they are managers/HR
    if leave_request.user_id != current_user.id:
        # Add manager/HR check here if needed
        pass
    
    return leave_request

@router.put("/requests/{request_id}", response_model=LeaveRequestResponse, summary="Update Leave Request Status", description="Approve/reject a leave request (manager/HR function)")
async def update_leave_request(
    request_id: int, 
    update_data: LeaveRequestUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    if leave_request is None:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    leave_request.status = update_data.status
    leave_request.approver_comments = update_data.approver_comments
    
    db.commit()
    db.refresh(leave_request)
    return leave_request

@router.put("/requests/{request_id}/approve", response_model=LeaveRequestResponse, summary="Approve Leave Request", description="Approve a leave request (manager function)")
async def approve_leave_request(
    request_id: int,
    approver_comments: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    if leave_request is None:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    # Verify manager permissions
    verify_manager_permission(db, current_user, leave_request.user_id)
    
    # Check if request is already processed
    if leave_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This leave request has already been processed"
        )
    
    try:
        # Double check leave balance before approving
        check_leave_balance(db, leave_request.user_id, leave_request.leave_type, leave_request.days_requested)
        
        # Update leave request status
        leave_request.status = "approved"
        leave_request.approver_comments = approver_comments
        
        # Update leave balance
        update_leave_balance(db, leave_request.user_id, leave_request.leave_type, leave_request.days_requested)
        
        db.commit()
        db.refresh(leave_request)
        return leave_request
        
    except HTTPException as e:
        if e.status_code == status.HTTP_400_BAD_REQUEST and "Insufficient" in str(e.detail):
            # Auto-reject the request with clear reason
            leave_request.status = "rejected"
            leave_request.approver_comments = f"Request automatically rejected: {str(e.detail)}"
            db.commit()
            db.refresh(leave_request)
            return leave_request
        else:
            # Re-raise other HTTP exceptions
            raise

@router.put("/requests/{request_id}/reject", response_model=LeaveRequestResponse, summary="Reject Leave Request", description="Reject a leave request (manager function)")
async def reject_leave_request(
    request_id: int,
    approver_comments: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    if leave_request is None:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    # Verify manager permissions
    verify_manager_permission(db, current_user, leave_request.user_id)
    
    # Check if request is already processed
    if leave_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This leave request has already been processed"
        )
    
    # Update leave request
    leave_request.status = "rejected"
    leave_request.approver_comments = approver_comments
    
    db.commit()
    db.refresh(leave_request)
    return leave_request

# Leave Balance Endpoints
@router.get("/balance", response_model=List[LeaveBalanceResponse], summary="Get My Leave Balance", description="Retrieve leave balance for current user")
async def get_my_leave_balance(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    leave_balances = db.query(LeaveBalance).filter(LeaveBalance.user_id == current_user.id).all()
    return leave_balances

@router.get("/balance/{user_id}", response_model=List[LeaveBalanceResponse], summary="Get Leave Balance by User ID", description="Retrieve leave balance for a specific user (manager/HR function)")
async def get_user_leave_balance(
    user_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    leave_balances = db.query(LeaveBalance).filter(LeaveBalance.user_id == user_id).all()
    return leave_balances

@router.delete("/requests/{request_id}", response_model=MessageResponse, summary="Delete Leave Request", description="Delete a leave request (only if pending)")
async def delete_leave_request(
    request_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    if leave_request is None:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    # Only allow deletion of own requests and only if pending
    if leave_request.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this request")
    
    if leave_request.status != "pending":
        raise HTTPException(status_code=400, detail="Can only delete pending requests")
    
    db.delete(leave_request)
    db.commit()
    return {"message": "Leave request deleted successfully"}

@router.get("/entitled/overtime", response_model=dict, summary="Get Overtime-based Leave Entitlement", description="Get your total leave days entitled from approved overtime for the current year.")
async def get_overtime_leave_entitlement(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    current_year = datetime.now().year
    total_ot_leave = db.query(func.coalesce(func.sum(OvertimeLeave.leave_days), 0)).filter(
        OvertimeLeave.user_id == current_user.id,
        OvertimeLeave.year == current_year
    ).scalar()
    return {
        "user_id": current_user.id,
        "year": current_year,
        "entitled_leave_days": total_ot_leave
    }

@router.get("/get_eligible_leaves", response_model=List[str], summary="Get Eligible Leave Types", description="Get a list of leave types the current user is eligible for.")
async def get_eligible_leave_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    eligible_types = [lt for lt in ALLOWED_LEAVE_TYPES if is_leave_type_eligible(current_user, lt)]
    return eligible_types
