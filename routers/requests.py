from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models import User, LeaveRequest, BankLetterRequest, VisaLetterRequest, OvertimeRequest, Payslip, PerformanceReview
from schemas import RequestSummary
from auth import get_current_active_user
from utils import is_manager, is_subordinate

router = APIRouter(prefix="/requests", tags=["All Requests"])

@router.get("/my-requests", response_model=List[RequestSummary], summary="Get All My Requests", description="Retrieve all requests (leave, bank letter, visa letter, overtime, payslip) for current user")
async def get_my_all_requests(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    requests = []
    
    # Get leave requests
    leave_requests = db.query(LeaveRequest).options(joinedload(LeaveRequest.user)).filter(LeaveRequest.user_id == current_user.id).all()
    for req in leave_requests:
        requests.append(RequestSummary(
            id=req.id,
            type=req.leave_type,
            request_type="leave",
            status=req.status,
            created_at=req.created_at,
            updated_at=req.updated_at,
            user_id=req.user.id,
            user_full_name=req.user.full_name,
            user_email=req.user.email
        ))
    
    # Get bank letter requests
    bank_requests = db.query(BankLetterRequest).options(joinedload(BankLetterRequest.user)).filter(BankLetterRequest.user_id == current_user.id).all()
    for req in bank_requests:
        requests.append(RequestSummary(
            id=req.id,
            type=req.type,
            request_type="bank_letter",
            status=req.status,
            created_at=req.created_at,
            updated_at=req.updated_at,
            user_id=req.user.id,
            user_full_name=req.user.full_name,
            user_email=req.user.email
        ))
    
    # Get visa letter requests
    visa_requests = db.query(VisaLetterRequest).options(joinedload(VisaLetterRequest.user)).filter(VisaLetterRequest.user_id == current_user.id).all()
    for req in visa_requests:
        requests.append(RequestSummary(
            id=req.id,
            type=req.type,
            request_type="visa_letter",
            status=req.status,
            created_at=req.created_at,
            updated_at=req.updated_at,
            user_id=req.user.id,
            user_full_name=req.user.full_name,
            user_email=req.user.email
        ))

    # Get overtime requests
    overtime_requests = db.query(OvertimeRequest).options(joinedload(OvertimeRequest.user)).filter(OvertimeRequest.user_id == current_user.id).all()
    for req in overtime_requests:
        requests.append(RequestSummary(
            id=req.id,
            type="Overtime",
            request_type="overtime",
            status=req.status,
            created_at=req.created_at,
            updated_at=req.updated_at,
            user_id=req.user.id,
            user_full_name=req.user.full_name,
            user_email=req.user.email
        ))

    # Get payslip requests
    payslip_requests = db.query(Payslip).options(joinedload(Payslip.user)).filter(Payslip.user_id == current_user.id).all()
    for req in payslip_requests:
        requests.append(RequestSummary(
            id=req.payslip_id,
            type=f"Payslip {req.month}/{req.year}",
            request_type="payslip",
            status=req.status,
            created_at=req.created_at,
            updated_at=req.updated_at,
            user_id=req.user.id,
            user_full_name=req.user.full_name,
            user_email=req.user.email
        ))

    # Get performance reviews
    performance_reviews = db.query(PerformanceReview).options(joinedload(PerformanceReview.user), joinedload(PerformanceReview.goal)).filter(PerformanceReview.user_id == current_user.id).all()
    for req in performance_reviews:
        requests.append(RequestSummary(
            id=req.review_id,
            type=f"Review for '{req.goal.title}'" if req.goal else "Performance Review",
            request_type="performance_review",
            status=req.status,
            created_at=req.created_at,
            updated_at=req.updated_at,
            user_id=req.user.id,
            user_full_name=req.user.full_name,
            user_email=req.user.email
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
    if not is_manager(db, current_user):
        raise HTTPException(status_code=403, detail="Only managers can view all requests.")
    requests = []
    
    # Get all leave requests
    leave_requests = db.query(LeaveRequest).options(joinedload(LeaveRequest.user)).offset(skip).limit(limit).all()
    for req in leave_requests:
        if is_subordinate(db, current_user, req.user_id):
            requests.append(RequestSummary(
                id=req.id,
                type=req.leave_type,
                request_type="leave",
                status=req.status,
                created_at=req.created_at,
                updated_at=req.updated_at,
                user_id=req.user.id,
                user_full_name=req.user.full_name,
                user_email=req.user.email
            ))
    
    # Get all bank letter requests
    bank_requests = db.query(BankLetterRequest).options(joinedload(BankLetterRequest.user)).offset(skip).limit(limit).all()
    for req in bank_requests:
        if is_subordinate(db, current_user, req.user_id):
            requests.append(RequestSummary(
                id=req.id,
                type=req.type,
                request_type="bank_letter",
                status=req.status,
                created_at=req.created_at,
                updated_at=req.updated_at,
                user_id=req.user.id,
                user_full_name=req.user.full_name,
                user_email=req.user.email
            ))
    
    # Get all visa letter requests
    visa_requests = db.query(VisaLetterRequest).options(joinedload(VisaLetterRequest.user)).offset(skip).limit(limit).all()
    for req in visa_requests:
        if is_subordinate(db, current_user, req.user_id):
            requests.append(RequestSummary(
                id=req.id,
                type=req.type,
                request_type="visa_letter",
                status=req.status,
                created_at=req.created_at,
                updated_at=req.updated_at,
                user_id=req.user.id,
                user_full_name=req.user.full_name,
                user_email=req.user.email
            ))

    # Get all overtime requests
    overtime_requests = db.query(OvertimeRequest).options(joinedload(OvertimeRequest.user)).offset(skip).limit(limit).all()
    for req in overtime_requests:
        if is_subordinate(db, current_user, req.user_id):
            requests.append(RequestSummary(
                id=req.id,
                type="Overtime",
                request_type="overtime",
                status=req.status,
                created_at=req.created_at,
                updated_at=req.updated_at,
                user_id=req.user.id,
                user_full_name=req.user.full_name,
                user_email=req.user.email
            ))

    # Get all payslip requests
    payslip_requests = db.query(Payslip).options(joinedload(Payslip.user)).offset(skip).limit(limit).all()
    for req in payslip_requests:
        if is_subordinate(db, current_user, req.user_id):
            requests.append(RequestSummary(
                id=req.payslip_id,
                type=f"Payslip {req.month}/{req.year}",
                request_type="payslip",
                status=req.status,
                created_at=req.created_at,
                updated_at=req.updated_at,
                user_id=req.user.id,
                user_full_name=req.user.full_name,
                user_email=req.user.email
            ))

    # Get all performance reviews
    performance_reviews = db.query(PerformanceReview).options(joinedload(PerformanceReview.user), joinedload(PerformanceReview.goal)).offset(skip).limit(limit).all()
    for req in performance_reviews:
        if is_subordinate(db, current_user, req.user_id):
            requests.append(RequestSummary(
                id=req.review_id,
                type=f"Review for '{req.goal.title}'" if req.goal else "Performance Review",
                request_type="performance_review",
                status=req.status,
                created_at=req.created_at,
                updated_at=req.updated_at,
                user_id=req.user.id,
                user_full_name=req.user.full_name,
                user_email=req.user.email
            ))
    
    # Sort by created_at descending
    requests.sort(key=lambda x: x.created_at, reverse=True)
    
    return requests

@router.get("/pending", response_model=List[RequestSummary], summary="Get Pending Requests", description="Retrieve all pending requests for approval (HR/Manager function)")
async def get_pending_requests(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    if not is_manager(db, current_user):
        raise HTTPException(status_code=403, detail="Only managers can view pending requests.")
    requests = []
    
    # Get pending leave requests
    leave_requests = db.query(LeaveRequest).options(joinedload(LeaveRequest.user)).filter(LeaveRequest.status == "pending").all()
    for req in leave_requests:
        if is_subordinate(db, current_user, req.user_id):
            requests.append(RequestSummary(
                id=req.id,
                type=req.leave_type,
                request_type="leave",
                status=req.status,
                created_at=req.created_at,
                updated_at=req.updated_at,
                user_id=req.user.id,
                user_full_name=req.user.full_name,
                user_email=req.user.email
            ))
    
    # Get pending bank letter requests
    bank_requests = db.query(BankLetterRequest).options(joinedload(BankLetterRequest.user)).filter(BankLetterRequest.status == "pending").all()
    for req in bank_requests:
        if is_subordinate(db, current_user, req.user_id):
            requests.append(RequestSummary(
                id=req.id,
                type=req.type,
                request_type="bank_letter",
                status=req.status,
                created_at=req.created_at,
                updated_at=req.updated_at,
                user_id=req.user.id,
                user_full_name=req.user.full_name,
                user_email=req.user.email
            ))
    
    # Get pending visa letter requests
    visa_requests = db.query(VisaLetterRequest).options(joinedload(VisaLetterRequest.user)).filter(VisaLetterRequest.status == "pending").all()
    for req in visa_requests:
        if is_subordinate(db, current_user, req.user_id):
            requests.append(RequestSummary(
                id=req.id,
                type=req.type,
                request_type="visa_letter",
                status=req.status,
                created_at=req.created_at,
                updated_at=req.updated_at,
                user_id=req.user.id,
                user_full_name=req.user.full_name,
                user_email=req.user.email
            ))

    # Get pending overtime requests
    overtime_requests = db.query(OvertimeRequest).options(joinedload(OvertimeRequest.user)).filter(OvertimeRequest.status == "pending").all()
    for req in overtime_requests:
        if is_subordinate(db, current_user, req.user_id):
            requests.append(RequestSummary(
                id=req.id,
                type="Overtime",
                request_type="overtime",
                status=req.status,
                created_at=req.created_at,
                updated_at=req.updated_at,
                user_id=req.user.id,
                user_full_name=req.user.full_name,
                user_email=req.user.email
            ))

    # Get pending payslip requests
    payslip_requests = db.query(Payslip).options(joinedload(Payslip.user)).filter(Payslip.status == "pending").all()
    for req in payslip_requests:
        if is_subordinate(db, current_user, req.user_id):
            requests.append(RequestSummary(
                id=req.payslip_id,
                type=f"Payslip {req.month}/{req.year}",
                request_type="payslip",
                status=req.status,
                created_at=req.created_at,
                updated_at=req.updated_at,
                user_id=req.user.id,
                user_full_name=req.user.full_name,
                user_email=req.user.email
            ))

    # Get pending performance reviews
    performance_reviews = db.query(PerformanceReview).options(joinedload(PerformanceReview.user), joinedload(PerformanceReview.goal)).filter(PerformanceReview.status == "pending").all()
    for req in performance_reviews:
        if is_subordinate(db, current_user, req.user_id):
            requests.append(RequestSummary(
                id=req.review_id,
                type=f"Review for '{req.goal.title}'" if req.goal else "Performance Review",
                request_type="performance_review",
                status=req.status,
                created_at=req.created_at,
                updated_at=req.updated_at,
                user_id=req.user.id,
                user_full_name=req.user.full_name,
                user_email=req.user.email
            ))
    
    # Sort by created_at ascending (oldest first for processing)
    requests.sort(key=lambda x: x.created_at)
    
    return requests 