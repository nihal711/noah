from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, LeaveRequest, LeaveBalance
from schemas import LeaveRequestCreate, LeaveRequestResponse, LeaveRequestUpdate, LeaveBalanceResponse, MessageResponse
from auth import get_current_active_user

router = APIRouter(prefix="/leave", tags=["Leave Management"])

# Leave Request Endpoints
@router.post("/requests", response_model=LeaveRequestResponse, summary="Apply for Leave", description="Submit a new leave request")
async def apply_leave(
    leave_request: LeaveRequestCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
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
    leave_requests = db.query(LeaveRequest).offset(skip).limit(limit).all()
    return leave_requests

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
    leave_request.manager_comments = update_data.manager_comments
    
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