from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from sqlalchemy import extract
from database import get_db
import models
import schemas
from auth import get_current_user
from api_utils.overtime import calculate_overtime_entitlement
from schemas import OvertimePreviewResponse, OvertimeRequestCreate, OvertimeRequestResponse, AttachmentCreate, AttachmentResponse
from models import Attachment, OvertimeLeave
from sqlalchemy.sql import func

router = APIRouter(
    prefix="/overtime",
    tags=["Overtime Management"]
)

@router.post("/preview", response_model=OvertimePreviewResponse, summary="Preview Overtime Entitlement", description="Preview how many leave days this OT request will grant, based on business rules.\n\nMultipliers: Weekday ×1.5, Weekend ×2.\nGrades 1–3: All hours, no cap. Grades 4–5: Max 4 hours/day. Leave = OT hours/8. Max 9 leave days/year.")
async def preview_overtime_request(
    request: OvertimeRequestCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Validation: date cannot be in the future
    today = datetime.now().date()
    if request.date > today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot preview overtime for a future date."
        )
    # Validation: only one OT request per day per user
    existing = db.query(models.OvertimeRequest).filter(
        models.OvertimeRequest.user_id == current_user.id,
        models.OvertimeRequest.date == request.date
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot preview overtime: a request (ID {existing.id}) already exists for this date."
        )
    # Calculate total approved OT leave days for this year
    year = request.date.year
    total_ot_leave = db.query(func.coalesce(func.sum(OvertimeLeave.leave_days), 0)).filter(
        OvertimeLeave.user_id == current_user.id,
        OvertimeLeave.year == year
    ).scalar()
    result = calculate_overtime_entitlement(current_user, request.date, request.hours, current_user.grade, 0)
    new_total = total_ot_leave + result['entitled_leave_days']
    message = result['message']
    if new_total > 9:
        message = (
            "Submitting this overtime request would exceed the maximum of 9 OT leave days per year. "
            "Your request will be auto-rejected. If you believe you need an exception, please contact your manager or HR."
        )
    return OvertimePreviewResponse(
        entitled_hours=result['entitled_hours'],
        entitled_leave_days=result['entitled_leave_days'],
        capped=result['capped'],
        message=message
    )

@router.post("/requests", response_model=OvertimeRequestResponse, summary="Create Overtime Request", description="Submit a new overtime request. Optionally attach a file. Preview leave entitlement before submitting.")
async def create_overtime_request(
    request: OvertimeRequestCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Validation: date cannot be in the future
    today = datetime.now().date()
    if request.date > today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot apply for overtime for a future date."
        )
    # Validation: only one OT request per day per user
    existing = db.query(models.OvertimeRequest).filter(
        models.OvertimeRequest.user_id == current_user.id,
        models.OvertimeRequest.date == request.date
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot apply for overtime: a request (ID {existing.id}) already exists for this date."
        )
    # Calculate total approved OT leave days for this year
    year = request.date.year
    total_ot_leave = db.query(func.coalesce(func.sum(OvertimeLeave.leave_days), 0)).filter(
        OvertimeLeave.user_id == current_user.id,
        OvertimeLeave.year == year
    ).scalar()
    result = calculate_overtime_entitlement(current_user, request.date, request.hours, current_user.grade, 0)
    new_total = total_ot_leave + result['entitled_leave_days']
    message = result['message']
    if new_total > 9:
        message = (
            "Submitting this overtime request would exceed the maximum of 9 OT leave days per year. "
            "Your request will be auto-rejected. If you believe you need an exception, please contact your manager or HR."
        )
    attachment_obj = None
    if request.attachment:
        attachment_obj = Attachment(
            file_name=request.attachment.fileName,
            file_type=request.attachment.fileType,
            file_desc=request.attachment.fileDesc,
            file_data=request.attachment.fileData
        )
        db.add(attachment_obj)
        db.flush()
    db_request = models.OvertimeRequest(
        user_id=current_user.id,
        date=request.date,
        hours=request.hours,
        reason=request.reason,
        attachment_id=attachment_obj.id if attachment_obj else None
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return OvertimeRequestResponse(
        id=db_request.id,
        user_id=db_request.user_id,
        date=db_request.date,
        hours=db_request.hours,
        reason=db_request.reason,
        status=db_request.status,
        approver_comments=db_request.approver_comments,
        created_at=db_request.created_at,
        updated_at=db_request.updated_at,
        message=message
    )

@router.get("/requests", response_model=List[OvertimeRequestResponse], summary="Get My Overtime Requests", description="Get your overtime requests with leave days granted for each.")
async def get_my_overtime_requests(
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.OvertimeRequest).filter(
        models.OvertimeRequest.user_id == current_user.id
    )
    if month and year:
        query = query.filter(
            extract('month', models.OvertimeRequest.date) == month,
            extract('year', models.OvertimeRequest.date) == year
        )
    requests = query.order_by(models.OvertimeRequest.date.desc()).all()

    responses = []
    for req in requests:
        leave = db.query(OvertimeLeave).filter(OvertimeLeave.overtime_request_id == req.id).first()
        leave_days_granted = leave.leave_days if leave else None
        responses.append(OvertimeRequestResponse(
            id=req.id,
            user_id=req.user_id,
            date=req.date,
            hours=req.hours,
            reason=req.reason,
            status=req.status,
            approver_comments=req.approver_comments,
            created_at=req.created_at,
            updated_at=req.updated_at,
            leave_days_granted=leave_days_granted
        ))
    return responses

@router.get("/requests/all", response_model=List[schemas.UserOvertimeRequests], summary="Get All Overtime Requests for Team", description="Managers: Get all overtime requests for your subordinates, with leave days granted for each.")
async def get_all_overtime_requests(
    user_id: Optional[int] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    team_members = db.query(models.User).filter(
        models.User.manager_id == current_user.id
    ).all()
    if not team_members:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have any team members"
        )
    team_member_ids = [member.id for member in team_members]
    if user_id:
        if user_id not in team_member_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view overtime requests for your team members"
            )
        team_members = [m for m in team_members if m.id == user_id]
    result = []
    for member in team_members:
        query = db.query(models.OvertimeRequest).filter(
            models.OvertimeRequest.user_id == member.id
        )
        if month is not None:
            query = query.filter(extract('month', models.OvertimeRequest.date) == month)
        if year is not None:
            query = query.filter(extract('year', models.OvertimeRequest.date) == year)
        requests = query.order_by(models.OvertimeRequest.date.desc()).all()
        reqs_with_leave = []
        for req in requests:
            leave = db.query(OvertimeLeave).filter(OvertimeLeave.overtime_request_id == req.id).first()
            leave_days_granted = leave.leave_days if leave else None
            reqs_with_leave.append(OvertimeRequestResponse(
                id=req.id,
                user_id=req.user_id,
                date=req.date,
                hours=req.hours,
                reason=req.reason,
                status=req.status,
                approver_comments=req.approver_comments,
                created_at=req.created_at,
                updated_at=req.updated_at,
                leave_days_granted=leave_days_granted
            ))
        if reqs_with_leave:
            result.append({
                "user_id": member.id,
                "username": member.username,
                "full_name": member.full_name,
                "requests": reqs_with_leave
            })
    return result

@router.put("/requests/{request_id}", response_model=schemas.OvertimeRequestResponse)
async def update_overtime_request(
    request_id: int,
    request_update: schemas.OvertimeRequestUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Update an overtime request.
    Only the request owner can update their request if it's still pending.
    All fields must be provided for a complete update.
    """
    db_request = db.query(models.OvertimeRequest).filter(
        models.OvertimeRequest.id == request_id,
        models.OvertimeRequest.user_id == current_user.id
    ).first()
    
    if not db_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Overtime request not found"
        )
    
    if db_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a request that is not pending"
        )
    
    # Update all fields
    db_request.date = request_update.date
    db_request.hours = request_update.hours
    db_request.reason = request_update.reason
    
    db.commit()
    db.refresh(db_request)
    
    return db_request

@router.delete("/requests/{request_id}")
async def delete_overtime_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Delete an overtime request.
    Only the request owner can delete their request if it's still pending.
    """
    db_request = db.query(models.OvertimeRequest).filter(
        models.OvertimeRequest.id == request_id,
        models.OvertimeRequest.user_id == current_user.id
    ).first()
    
    if not db_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Overtime request not found"
        )
    
    if db_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a request that is not pending"
        )
    
    db.delete(db_request)
    db.commit()
    
    return {"message": "Overtime request deleted successfully"}

@router.put("/requests/{request_id}/approve", response_model=OvertimeRequestResponse, summary="Approve Overtime Request", description="Approve an overtime request. Only managers can approve. On approval, leave entitlement is granted if within cap. If the request would exceed the cap, only enough leave days to reach the cap are granted, and the rest are not converted.")
async def approve_overtime_request(
    request_id: int,
    approver_comments: str = Body(None, embed=True),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_request = db.query(models.OvertimeRequest).filter(
        models.OvertimeRequest.id == request_id
    ).first()
    if not db_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Overtime request not found"
        )
    if db_request.user.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only approve overtime requests for your direct subordinates"
        )
    if db_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request is already {db_request.status}"
        )
    year = db_request.date.year
    # Get total leave days already granted for this year
    total_leave_days = db.query(OvertimeLeave).filter(
        OvertimeLeave.user_id == db_request.user_id,
        OvertimeLeave.year == year
    ).with_entities(func.coalesce(func.sum(OvertimeLeave.leave_days), 0)).scalar()
    # Calculate entitlement for this request
    result = calculate_overtime_entitlement(db_request.user, db_request.date, db_request.hours, db_request.user.grade, 0)
    request_leave_days = result['entitled_leave_days']
    request_hours = result['entitled_hours']
    new_total = total_leave_days + request_leave_days
    if request_leave_days <= 0:
        db_request.status = "rejected"
        db_request.approver_comments = (approver_comments or "") + "\nAuto-rejected: No entitled leave days for this request."
        db.commit()
        db.refresh(db_request)
        return OvertimeRequestResponse(
            id=db_request.id,
            user_id=db_request.user_id,
            date=db_request.date,
            hours=db_request.hours,
            reason=db_request.reason,
            status=db_request.status,
            approver_comments=db_request.approver_comments,
            created_at=db_request.created_at,
            updated_at=db_request.updated_at
        )
    # Partial approval logic
    if new_total > 9:
        grantable_days = max(0, 9 - total_leave_days)
        if grantable_days > 0:
            grantable_hours = grantable_days * 8
            # Only grant up to the cap
            overtime_leave = OvertimeLeave(
                user_id=db_request.user_id,
                overtime_request_id=db_request.id,
                year=year,
                ot_hours=grantable_hours,
                leave_days=grantable_days
            )
            db.add(overtime_leave)
            db_request.status = "approved"
            extra_days = request_leave_days - grantable_days
            extra_hours = request_hours - grantable_hours
            db_request.approver_comments = (
                (approver_comments or "") +
                f"\nPartial approval: Only {grantable_days:.2f} leave days ({grantable_hours:.2f} OT hours) granted to reach the 9-day cap. "
                f"{extra_days:.2f} leave days ({extra_hours:.2f} OT hours) from this request were not converted due to the cap. "
                f"If you need more, contact HR. (HR: hr@example.com)"
            )
        else:
            # Already at cap, reject
            db_request.status = "rejected"
            db_request.approver_comments = (
                (approver_comments or "") +
                "\nAuto-rejected: Approving this request would exceed the maximum of 9 OT leave days per year. Please contact HR for exceptions. (HR: hr@example.com)"
            )
        db.commit()
        db.refresh(db_request)
        return OvertimeRequestResponse(
            id=db_request.id,
            user_id=db_request.user_id,
            date=db_request.date,
            hours=db_request.hours,
            reason=db_request.reason,
            status=db_request.status,
            approver_comments=db_request.approver_comments,
            created_at=db_request.created_at,
            updated_at=db_request.updated_at
        )
    # Full approval
    overtime_leave = OvertimeLeave(
        user_id=db_request.user_id,
        overtime_request_id=db_request.id,
        year=year,
        ot_hours=request_hours,
        leave_days=request_leave_days
    )
    db.add(overtime_leave)
    db_request.status = "approved"
    db_request.approver_comments = (approver_comments or "") + f"\n{result['message']}"
    db.commit()
    db.refresh(db_request)
    return OvertimeRequestResponse(
        id=db_request.id,
        user_id=db_request.user_id,
        date=db_request.date,
        hours=db_request.hours,
        reason=db_request.reason,
        status=db_request.status,
        approver_comments=db_request.approver_comments,
        created_at=db_request.created_at,
        updated_at=db_request.updated_at
    )

@router.put("/requests/{request_id}/reject", response_model=schemas.OvertimeRequestResponse)
async def reject_overtime_request(
    request_id: int,
    approver_comments: str = Body(None, embed=True),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Reject an overtime request.
    Only managers can reject requests for their subordinates.
    """
    db_request = db.query(models.OvertimeRequest).filter(
        models.OvertimeRequest.id == request_id
    ).first()
    
    if not db_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Overtime request not found"
        )
    
    # Verify the current user is the manager of the request's user
    if db_request.user.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only reject overtime requests for your direct subordinates"
        )
    
    if db_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request is already {db_request.status}"
        )
    
    db_request.status = "rejected"
    db_request.approver_comments = approver_comments
    
    db.commit()
    db.refresh(db_request)
    
    return db_request

@router.patch("/requests/{request_id}", response_model=schemas.OvertimeRequestResponse)
async def patch_overtime_request(
    request_id: int,
    request_update: schemas.OvertimeRequestPartialUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Partially update an overtime request.
    Only the request owner can update their request if it's still pending.
    Only the fields provided in the request will be updated.
    """
    db_request = db.query(models.OvertimeRequest).filter(
        models.OvertimeRequest.id == request_id,
        models.OvertimeRequest.user_id == current_user.id
    ).first()
    
    if not db_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Overtime request not found"
        )
    
    if db_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a request that is not pending"
        )
    

    if request_update.date is not None:
        db_request.date = request_update.date
    if request_update.hours is not None:
        db_request.hours = request_update.hours
    if request_update.reason is not None:
        db_request.reason = request_update.reason
    
    db.commit()
    db.refresh(db_request)
    
    return db_request 