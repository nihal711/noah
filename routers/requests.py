from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, LeaveRequest, BankLetterRequest, VisaLetterRequest
from schemas import RequestSummary
from auth import get_current_active_user

router = APIRouter(prefix="/requests", tags=["All Requests"])

@router.get("/my-requests", response_model=List[RequestSummary], summary="Get All My Requests", description="Retrieve all requests (leave, bank letter, visa letter) for current user")
async def get_my_all_requests(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    requests = []
    
    # Get leave requests
    leave_requests = db.query(LeaveRequest).filter(LeaveRequest.user_id == current_user.id).all()
    for req in leave_requests:
        requests.append(RequestSummary(
            id=req.id,
            type=req.leave_type,
            request_type="leave",
            status=req.status,
            created_at=req.created_at,
            updated_at=req.updated_at
        ))
    
    # Get bank letter requests
    bank_requests = db.query(BankLetterRequest).filter(BankLetterRequest.user_id == current_user.id).all()
    for req in bank_requests:
        requests.append(RequestSummary(
            id=req.id,
            type=req.type,
            request_type="bank_letter",
            status=req.status,
            created_at=req.created_at,
            updated_at=req.updated_at
        ))
    
    # Get visa letter requests
    visa_requests = db.query(VisaLetterRequest).filter(VisaLetterRequest.user_id == current_user.id).all()
    for req in visa_requests:
        requests.append(RequestSummary(
            id=req.id,
            type=req.type,
            request_type="visa_letter",
            status=req.status,
            created_at=req.created_at,
            updated_at=req.updated_at
        ))
    
    # Sort by created_at descending
    requests.sort(key=lambda x: x.created_at, reverse=True)
    
    return requests

@router.get("/all-requests", response_model=List[RequestSummary], summary="Get All Requests", description="Retrieve all requests from all users (HR/Manager function)")
async def get_all_requests(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    requests = []
    
    # Get all leave requests
    leave_requests = db.query(LeaveRequest).offset(skip).limit(limit).all()
    for req in leave_requests:
        requests.append(RequestSummary(
            id=req.id,
            type=req.leave_type,
            request_type="leave",
            status=req.status,
            created_at=req.created_at,
            updated_at=req.updated_at
        ))
    
    # Get all bank letter requests
    bank_requests = db.query(BankLetterRequest).offset(skip).limit(limit).all()
    for req in bank_requests:
        requests.append(RequestSummary(
            id=req.id,
            type=req.type,
            request_type="bank_letter",
            status=req.status,
            created_at=req.created_at,
            updated_at=req.updated_at
        ))
    
    # Get all visa letter requests
    visa_requests = db.query(VisaLetterRequest).offset(skip).limit(limit).all()
    for req in visa_requests:
        requests.append(RequestSummary(
            id=req.id,
            type=req.type,
            request_type="visa_letter",
            status=req.status,
            created_at=req.created_at,
            updated_at=req.updated_at
        ))
    
    # Sort by created_at descending
    requests.sort(key=lambda x: x.created_at, reverse=True)
    
    return requests

@router.get("/pending", response_model=List[RequestSummary], summary="Get Pending Requests", description="Retrieve all pending requests for approval (HR/Manager function)")
async def get_pending_requests(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    requests = []
    
    # Get pending leave requests
    leave_requests = db.query(LeaveRequest).filter(LeaveRequest.status == "pending").all()
    for req in leave_requests:
        requests.append(RequestSummary(
            id=req.id,
            type=req.leave_type,
            request_type="leave",
            status=req.status,
            created_at=req.created_at,
            updated_at=req.updated_at
        ))
    
    # Get pending bank letter requests
    bank_requests = db.query(BankLetterRequest).filter(BankLetterRequest.status == "pending").all()
    for req in bank_requests:
        requests.append(RequestSummary(
            id=req.id,
            type=req.type,
            request_type="bank_letter",
            status=req.status,
            created_at=req.created_at,
            updated_at=req.updated_at
        ))
    
    # Get pending visa letter requests
    visa_requests = db.query(VisaLetterRequest).filter(VisaLetterRequest.status == "pending").all()
    for req in visa_requests:
        requests.append(RequestSummary(
            id=req.id,
            type=req.type,
            request_type="visa_letter",
            status=req.status,
            created_at=req.created_at,
            updated_at=req.updated_at
        ))
    
    # Sort by created_at ascending (oldest first for processing)
    requests.sort(key=lambda x: x.created_at)
    
    return requests 