from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime
import calendar

from database import get_db
from models import Payslip, User
from schemas import PayslipCreate, PayslipResponse, PayslipUpdate
from auth import get_current_user
from utils import verify_manager_permission

router = APIRouter(
    prefix="/payslips",
    tags=["Payslips Management"]
)

@router.get("/getpayslipperiod")
async def get_payslip_periods(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year

    periods = []

    if current_month == 1:
        # If January, show all months of previous year
        year = current_year - 1
        for month in range(1, 13):
            month_name = calendar.month_name[month]
            periods.append({
                "label": f"{month_name} {year}",
                "month": month,
                "month_name": month_name,
                "year": year
            })
    else:
        # Otherwise, show Jan to previous month of current year
        for month in range(1, current_month):
            month_name = calendar.month_name[month]
            periods.append({
                "label": f"{month_name} {current_year}",
                "month": month,
                "month_name": month_name,
                "year": current_year
            })

    return periods

@router.post("/generate")
async def generate_payslip(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if payslip already exists for this month/year
    existing_payslip = db.query(Payslip).filter(
        Payslip.user_id == current_user.id,
        Payslip.month == month,
        Payslip.year == year
    ).first()
    
    if existing_payslip:
        raise HTTPException(status_code=400, detail="Payslip already exists for this period")
    
    # Create sample payslip data
    basic_salary = 5000.0  # This should come from user's actual salary
    allowances = 1000.0
    deductions = 500.0
    net_salary = basic_salary + allowances - deductions
    
    payslip = Payslip(
        user_id=current_user.id,
        month=month,
        year=year,
        basic_salary=basic_salary,
        allowances=allowances,
        deductions=deductions,
        net_salary=net_salary
    )
    
    db.add(payslip)
    db.commit()
    db.refresh(payslip)
    
    return payslip

@router.get("")
async def get_payslips(
    year: Optional[int] = Query(None, ge=2000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if year is None:
        year = datetime.now().year

    query = db.query(Payslip).filter(Payslip.year == year)
    
    # If user is not a manager, only show their payslips
    if not current_user.manager_id:  # If user has no manager, they can see all their subordinates' payslips
        query = query.filter(Payslip.user_id == current_user.id)
    else:  # If user has a manager, they can only see their own payslips
        query = query.filter(Payslip.user_id == current_user.id)
    
    payslips = query.order_by(Payslip.year.desc(), Payslip.month.desc()).all()
    
    return payslips

@router.get("/get_single")
async def get_single_payslip(
    year: int = Query(..., ge=2000),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    payslip = db.query(Payslip).filter(
        Payslip.user_id == current_user.id,
        Payslip.year == year,
        Payslip.month == month
    ).first()
    if not payslip:
        return {"message": "Payslip not generated for the given month and year"}
    return payslip 

@router.get("/{payslip_id}")
async def get_payslip_details(
    payslip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    payslip = db.query(Payslip).filter(Payslip.payslip_id == payslip_id).first()
    
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    
    # Check if user has permission to view this payslip
    if payslip.user_id != current_user.id:
        # If not the owner, verify manager permissions
        verify_manager_permission(db, current_user, payslip.user_id)
    
    return payslip

@router.delete("/{payslip_id}")
async def delete_payslip(
    payslip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    payslip = db.query(Payslip).filter(Payslip.payslip_id == payslip_id).first()
    
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    
    if payslip.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this payslip")
    
    if payslip.status != "pending":
        raise HTTPException(status_code=400, detail="Cannot delete approved or rejected payslip")
    
    db.delete(payslip)
    db.commit()
    
    return {"message": "Payslip deleted successfully"}

@router.put("/{payslip_id}/approve")
async def approve_payslip(
    payslip_id: int,
    approver_comments: str = Body(None, embed=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    payslip = db.query(Payslip).filter(Payslip.payslip_id == payslip_id).first()
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    if payslip.user.manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the employee's manager can approve payslips")
    if payslip.status != "pending":
        raise HTTPException(status_code=400, detail="Payslip is not in pending status")
    payslip.status = "approved"
    payslip.approved_by = current_user.id
    payslip.approved_at = datetime.now()
    payslip.approver_comments = approver_comments
    db.commit()
    db.refresh(payslip)
    return payslip

@router.put("/{payslip_id}/reject")
async def reject_payslip(
    payslip_id: int,
    approver_comments: str = Body(None, embed=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    payslip = db.query(Payslip).filter(Payslip.payslip_id == payslip_id).first()
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    if payslip.user.manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the employee's manager can reject payslips")
    if payslip.status != "pending":
        raise HTTPException(status_code=400, detail="Payslip is not in pending status")
    payslip.status = "rejected"
    payslip.approved_by = current_user.id
    payslip.approved_at = datetime.now()
    payslip.approver_comments = approver_comments
    db.commit()
    db.refresh(payslip)
    return payslip 
