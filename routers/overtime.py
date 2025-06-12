from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from sqlalchemy import extract
from database import get_db
import models
import schemas
from auth import get_current_user

router = APIRouter(
    prefix="/overtime",
    tags=["Overtime Management"]
)

@router.post("/requests", response_model=schemas.OvertimeRequestResponse)
async def create_overtime_request(
    request: schemas.OvertimeRequestCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Submit a new overtime request.
    """
    db_request = models.OvertimeRequest(
        user_id=current_user.id,
        date=request.date,
        hours=request.hours,
        reason=request.reason
    )
    
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    
    return db_request

@router.get("/requests", response_model=List[schemas.OvertimeRequestResponse])
async def get_my_overtime_requests(
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get overtime records for the current user.
    If month and year are provided, filter by those parameters.
    """
    query = db.query(models.OvertimeRequest).filter(
        models.OvertimeRequest.user_id == current_user.id
    )
    
    if month and year:
        query = query.filter(
            extract('month', models.OvertimeRequest.date) == month,
            extract('year', models.OvertimeRequest.date) == year
        )
    
    return query.order_by(models.OvertimeRequest.date.desc()).all()

@router.get("/requests/all", response_model=List[schemas.UserOvertimeRequests])
async def get_all_overtime_requests(
    user_id: Optional[int] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get all overtime records for team members (manager only), grouped by user.
    Can filter by:
    - user_id: Get requests for a specific team member
    - month: Get requests for a specific month (1-12) across all years
    - year: Get requests for a specific year
    - month and year: Get requests for a specific month and year
    """
    # Get all users who report to this manager
    team_members = db.query(models.User).filter(
        models.User.manager_id == current_user.id
    ).all()
    
    if not team_members:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have any team members"
        )
    
    team_member_ids = [member.id for member in team_members]
    
    # If specific user_id is provided, verify they are a team member
    if user_id:
        if user_id not in team_member_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view overtime requests for your team members"
            )
        team_members = [m for m in team_members if m.id == user_id]
    
    result = []
    for member in team_members:
        # Get overtime requests for this team member
        query = db.query(models.OvertimeRequest).filter(
            models.OvertimeRequest.user_id == member.id
        )
        
        # Apply date filters if provided
        if month is not None:
            query = query.filter(extract('month', models.OvertimeRequest.date) == month)
        if year is not None:
            query = query.filter(extract('year', models.OvertimeRequest.date) == year)
        
        requests = query.order_by(models.OvertimeRequest.date.desc()).all()
        
        # Only include users who have requests
        if requests:
            result.append({
                "user_id": member.id,
                "username": member.username,
                "full_name": member.full_name,
                "requests": requests
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

@router.put("/requests/{request_id}/approve", response_model=schemas.OvertimeRequestResponse)
async def approve_overtime_request(
    request_id: int,
    approval: schemas.OvertimeRequestApproval,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Approve an overtime request.
    Only managers can approve requests for their subordinates.
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
            detail="You can only approve overtime requests for your direct subordinates"
        )
    
    if db_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request is already {db_request.status}"
        )
    
    db_request.status = "approved"
    db_request.manager_comments = approval.manager_comments
    
    db.commit()
    db.refresh(db_request)
    
    return db_request

@router.put("/requests/{request_id}/reject", response_model=schemas.OvertimeRequestResponse)
async def reject_overtime_request(
    request_id: int,
    rejection: schemas.OvertimeRequestRejection,
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
    db_request.manager_comments = rejection.manager_comments
    
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