from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from database import get_db
from models import User, BankLetterRequest, Attachment
from schemas import BankLetterRequestCreate, BankLetterRequestResponse, BankLetterRequestUpdate, MessageResponse
from auth import get_current_active_user
from utils import verify_manager_permission

router = APIRouter(prefix="/bank-letter", tags=["Bank Letter Requests"])

@router.post("/", response_model=BankLetterRequestResponse, summary="Request Bank Letter", description="Submit a new bank letter request with attachments")
async def request_bank_letter(
    bank_letter_request: BankLetterRequestCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    # Create the bank letter request
    db_bank_letter_request = BankLetterRequest(
        user_id=current_user.id,
        bank_name=bank_letter_request.bankName,
        type=bank_letter_request.type,
        additional_details=bank_letter_request.comment
    )
    db.add(db_bank_letter_request)
    db.flush()  # Get the ID
    
    # Create attachments
    for attachment_data in bank_letter_request.attachments:
        attachment = Attachment(
            file_name=attachment_data.fileName,
            file_type=attachment_data.fileType,
            file_desc=attachment_data.fileDesc,
            file_data=attachment_data.fileData,
            bank_letter_request_id=db_bank_letter_request.id
        )
        db.add(attachment)
    
    db.commit()
    db.refresh(db_bank_letter_request)
    return db_bank_letter_request

@router.get("/", response_model=List[BankLetterRequestResponse], summary="Get My Bank Letter Requests", description="Retrieve all bank letter requests for current user")
async def get_my_bank_letter_requests(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    bank_letter_requests = db.query(BankLetterRequest).filter(BankLetterRequest.user_id == current_user.id).all()
    return bank_letter_requests

@router.get("/all", response_model=List[BankLetterRequestResponse], summary="Get All Bank Letter Requests", description="Retrieve all bank letter requests (HR function)")
async def get_all_bank_letter_requests(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    bank_letter_requests = db.query(BankLetterRequest).offset(skip).limit(limit).all()
    return bank_letter_requests

@router.get("/{request_id}", response_model=BankLetterRequestResponse, summary="Get Bank Letter Request by ID", description="Retrieve a specific bank letter request by ID")
async def get_bank_letter_request(
    request_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    bank_letter_request = db.query(BankLetterRequest).filter(BankLetterRequest.id == request_id).first()
    if bank_letter_request is None:
        raise HTTPException(status_code=404, detail="Bank letter request not found")
    
    # Users can only see their own requests unless they are HR
    if bank_letter_request.user_id != current_user.id:
        # Add HR role check here if needed
        pass
    
    return bank_letter_request

@router.put("/{request_id}", response_model=BankLetterRequestResponse, summary="Update Bank Letter Request Status", description="Approve/reject a bank letter request (HR function)")
async def update_bank_letter_request(
    request_id: int, 
    update_data: BankLetterRequestUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    bank_letter_request = db.query(BankLetterRequest).filter(BankLetterRequest.id == request_id).first()
    if bank_letter_request is None:
        raise HTTPException(status_code=404, detail="Bank letter request not found")
    
    bank_letter_request.status = update_data.status
    bank_letter_request.hr_comments = update_data.hr_comments
    
    db.commit()
    db.refresh(bank_letter_request)
    return bank_letter_request

@router.delete("/{request_id}", response_model=MessageResponse, summary="Delete Bank Letter Request", description="Delete a bank letter request (only if pending)")
async def delete_bank_letter_request(
    request_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    bank_letter_request = db.query(BankLetterRequest).filter(BankLetterRequest.id == request_id).first()
    if bank_letter_request is None:
        raise HTTPException(status_code=404, detail="Bank letter request not found")
    
    # Only allow deletion of own requests and only if pending
    if bank_letter_request.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this request")
    
    if bank_letter_request.status != "pending":
        raise HTTPException(status_code=400, detail="Can only delete pending requests")
    
    db.delete(bank_letter_request)
    db.commit()
    return {"message": "Bank letter request deleted successfully"}

def is_manager(db: Session, user: User) -> bool:
    """Check if user is a manager (has subordinates)"""
    # Check if any user has this user as their manager
    subordinates = db.query(User).filter(User.manager_id == user.id).first()
    return subordinates is not None

def is_subordinate(db: Session, manager: User, user_id: int) -> bool:
    """Check if user_id is a subordinate of the manager"""
    # Get the target user
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        return False
    # Check if target user's manager is the given manager
    return target_user.manager_id == manager.id

@router.put("/{request_id}/approve", response_model=BankLetterRequestResponse)
async def approve_bank_letter_request(
    request_id: int,
    manager_comments: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Approve a bank letter request.
    Only managers can approve requests for their subordinates.
    """
    # Get the request
    bank_letter_request = db.query(BankLetterRequest).filter(BankLetterRequest.id == request_id).first()
    if not bank_letter_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank letter request not found"
        )
    
    # Check if request is already approved or rejected
    if bank_letter_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request is already {bank_letter_request.status}"
        )
    
    # Verify manager permissions
    verify_manager_permission(db, current_user, bank_letter_request.user_id)
    
    # Update the request
    bank_letter_request.status = "approved"
    bank_letter_request.hr_comments = manager_comments
    
    db.commit()
    db.refresh(bank_letter_request)
    return bank_letter_request

@router.put("/{request_id}/reject", response_model=BankLetterRequestResponse)
async def reject_bank_letter_request(
    request_id: int,
    manager_comments: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Reject a bank letter request.
    Only managers can reject requests for their subordinates.
    """
    # Get the request
    bank_letter_request = db.query(BankLetterRequest).filter(BankLetterRequest.id == request_id).first()
    if not bank_letter_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank letter request not found"
        )
    
    # Check if request is already approved or rejected
    if bank_letter_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request is already {bank_letter_request.status}"
        )
    
    # Verify manager permissions
    verify_manager_permission(db, current_user, bank_letter_request.user_id)
    
    # Update the request
    bank_letter_request.status = "rejected"
    bank_letter_request.hr_comments = manager_comments
    
    db.commit()
    db.refresh(bank_letter_request)
    return bank_letter_request 