from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from database import get_db
from models import User, VisaLetterRequest, Attachment
from schemas import VisaLetterRequestCreate, VisaLetterRequestResponse, VisaLetterRequestUpdate, MessageResponse
from auth import get_current_active_user

router = APIRouter(prefix="/visa-letter", tags=["Visa Letter Requests"])

@router.post("/", response_model=VisaLetterRequestResponse, summary="Request Visa Letter", description="Submit a new visa letter request with attachments")
async def request_visa_letter(
    visa_letter_request: VisaLetterRequestCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    # Create the visa letter request
    db_visa_letter_request = VisaLetterRequest(
        user_id=current_user.id,
        type=visa_letter_request.type,
        comment=visa_letter_request.comment,
        language=visa_letter_request.language,
        addressed_to=visa_letter_request.addressedTo,
        country=visa_letter_request.country
    )
    db.add(db_visa_letter_request)
    db.flush()  # Get the ID
    
    # Create attachments
    for attachment_data in visa_letter_request.attachments:
        attachment = Attachment(
            file_name=attachment_data.fileName,
            file_type=attachment_data.fileType,
            file_desc=attachment_data.fileDesc,
            file_data=attachment_data.fileData,
            visa_letter_request_id=db_visa_letter_request.id
        )
        db.add(attachment)
    
    db.commit()
    db.refresh(db_visa_letter_request)
    return db_visa_letter_request

@router.get("/", response_model=List[VisaLetterRequestResponse], summary="Get My Visa Letter Requests", description="Retrieve all visa letter requests for current user")
async def get_my_visa_letter_requests(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    visa_letter_requests = db.query(VisaLetterRequest).filter(VisaLetterRequest.user_id == current_user.id).all()
    return visa_letter_requests

@router.get("/all", response_model=List[VisaLetterRequestResponse], summary="Get All Visa Letter Requests", description="Retrieve all visa letter requests (HR function)")
async def get_all_visa_letter_requests(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    visa_letter_requests = db.query(VisaLetterRequest).offset(skip).limit(limit).all()
    return visa_letter_requests

@router.get("/{request_id}", response_model=VisaLetterRequestResponse, summary="Get Visa Letter Request by ID", description="Retrieve a specific visa letter request by ID")
async def get_visa_letter_request(
    request_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    visa_letter_request = db.query(VisaLetterRequest).filter(VisaLetterRequest.id == request_id).first()
    if visa_letter_request is None:
        raise HTTPException(status_code=404, detail="Visa letter request not found")
    
    # Users can only see their own requests unless they are HR
    if visa_letter_request.user_id != current_user.id:
        # Add HR role check here if needed
        pass
    
    return visa_letter_request

@router.put("/{request_id}", response_model=VisaLetterRequestResponse, summary="Update Visa Letter Request Status", description="Approve/reject a visa letter request (HR function)")
async def update_visa_letter_request(
    request_id: int, 
    update_data: VisaLetterRequestUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    visa_letter_request = db.query(VisaLetterRequest).filter(VisaLetterRequest.id == request_id).first()
    if visa_letter_request is None:
        raise HTTPException(status_code=404, detail="Visa letter request not found")
    
    visa_letter_request.status = update_data.status
    visa_letter_request.approver_comments = update_data.approver_comments
    
    db.commit()
    db.refresh(visa_letter_request)
    return visa_letter_request

@router.delete("/{request_id}", response_model=MessageResponse, summary="Delete Visa Letter Request", description="Delete a visa letter request (only if pending)")
async def delete_visa_letter_request(
    request_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    visa_letter_request = db.query(VisaLetterRequest).filter(VisaLetterRequest.id == request_id).first()
    if visa_letter_request is None:
        raise HTTPException(status_code=404, detail="Visa letter request not found")
    
    # Only allow deletion of own requests and only if pending
    if visa_letter_request.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this request")
    
    if visa_letter_request.status != "pending":
        raise HTTPException(status_code=400, detail="Can only delete pending requests")
    
    db.delete(visa_letter_request)
    db.commit()
    return {"message": "Visa letter request deleted successfully"}

@router.put("/{request_id}/approve", response_model=VisaLetterRequestResponse)
async def approve_visa_letter_request(
    request_id: int,
    approver_comments: str = Body(None, embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    visa_letter_request = db.query(VisaLetterRequest).filter(VisaLetterRequest.id == request_id).first()
    if visa_letter_request is None:
        raise HTTPException(status_code=404, detail="Visa letter request not found")
    visa_letter_request.status = "approved"
    visa_letter_request.approver_comments = approver_comments
    db.commit()
    db.refresh(visa_letter_request)
    return visa_letter_request

@router.put("/{request_id}/reject", response_model=VisaLetterRequestResponse)
async def reject_visa_letter_request(
    request_id: int,
    approver_comments: str = Body(None, embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    visa_letter_request = db.query(VisaLetterRequest).filter(VisaLetterRequest.id == request_id).first()
    if visa_letter_request is None:
        raise HTTPException(status_code=404, detail="Visa letter request not found")
    visa_letter_request.status = "rejected"
    visa_letter_request.approver_comments = approver_comments
    db.commit()
    db.refresh(visa_letter_request)
    return visa_letter_request 