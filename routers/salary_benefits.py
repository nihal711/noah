from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, SalaryStructure, Benefit, BenefitEnrollment
from schemas import (
    SalaryStructureCreate, SalaryStructureUpdate, SalaryStructureResponse,
    BenefitResponse, BenefitEnrollmentCreate, BenefitEnrollmentResponse,
    BenefitEnrollmentUpdate
)
from auth import get_current_active_user
from datetime import datetime
import logging
from utils import verify_manager_permission

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/salary", tags=["Salary and Benefits"])

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

# Salary Structure APIs
@router.post("/structure", response_model=SalaryStructureResponse)
async def create_salary_structure(
    salary: SalaryStructureCreate,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    logger.info(f"Creating salary structure for user {user_id} by user {current_user.id}")
    
    # Verify manager permissions
    verify_manager_permission(db, current_user, user_id)
    
    # Check if user already has a salary structure
    existing = db.query(SalaryStructure).filter(SalaryStructure.user_id == user_id).first()
    if existing:
        logger.warning(f"Salary structure already exists for user {user_id}")
        raise HTTPException(status_code=400, detail="Salary structure already exists for this user")
    
    db_salary = SalaryStructure(
        user_id=user_id,
        basic_salary=salary.basic_salary,
        allowances=salary.allowances,
        deductions=salary.deductions,
        effective_date=salary.effective_date
    )
    db.add(db_salary)
    db.commit()
    db.refresh(db_salary)
    logger.info(f"Successfully created salary structure for user {user_id}")
    return db_salary

@router.get("/structure", response_model=SalaryStructureResponse)
async def get_my_salary_structure(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    logger.info(f"User {current_user.id} requesting their salary structure")
    salary = db.query(SalaryStructure).filter(SalaryStructure.user_id == current_user.id).first()
    if not salary:
        logger.warning(f"Salary structure not found for user {current_user.id}")
        raise HTTPException(status_code=404, detail="Salary structure not found")
    return salary

@router.get("/structure/{user_id}", response_model=SalaryStructureResponse)
async def get_user_salary_structure(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    logger.info(f"User {current_user.id} requesting salary structure for user {user_id}")
    
    # Verify manager permissions
    verify_manager_permission(db, current_user, user_id)
    
    salary = db.query(SalaryStructure).filter(SalaryStructure.user_id == user_id).first()
    if not salary:
        logger.warning(f"Salary structure not found for user {user_id}")
        raise HTTPException(status_code=404, detail="Salary structure not found")
    return salary

@router.put("/structure/{user_id}", response_model=SalaryStructureResponse)
async def update_salary_structure(
    user_id: int,
    salary: SalaryStructureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    logger.info(f"User {current_user.id} attempting to update salary structure for user {user_id}")
    
    # Verify manager permissions
    verify_manager_permission(db, current_user, user_id)
    
    db_salary = db.query(SalaryStructure).filter(SalaryStructure.user_id == user_id).first()
    if not db_salary:
        logger.warning(f"Salary structure not found for user {user_id}")
        raise HTTPException(status_code=404, detail="Salary structure not found")
    
    for key, value in salary.dict().items():
        setattr(db_salary, key, value)
    
    db.commit()
    db.refresh(db_salary)
    logger.info(f"Successfully updated salary structure for user {user_id}")
    return db_salary

# Benefits APIs
@router.get("/benefits", response_model=List[BenefitResponse])
async def list_benefits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    benefits = db.query(Benefit).filter(Benefit.is_active == True).all()
    return benefits


@router.get("/benefits/gradewise")
async def list_benefits_gradewise(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all benefits grouped by grade."""
    benefits = db.query(Benefit).filter(Benefit.is_active == True).all()
    gradewise = {}
    for benefit in benefits:
        if benefit.grades:
            for grade in benefit.grades:
                gradewise.setdefault(grade, []).append(BenefitResponse.model_validate(benefit))
    gradewise = dict(sorted(gradewise.items(), key=lambda x: x[0]))
    return gradewise

@router.post("/benefits/enroll", response_model=BenefitEnrollmentResponse)
async def enroll_in_benefit(
    enrollment: BenefitEnrollmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Check if benefit exists and is active
    benefit = db.query(Benefit).filter(
        Benefit.benefit_id == enrollment.benefit_id,
        Benefit.is_active == True
    ).first()
    if not benefit:
        raise HTTPException(status_code=404, detail="Benefit not found or inactive")
    
    # Check if user is already enrolled
    existing = db.query(BenefitEnrollment).filter(
        BenefitEnrollment.user_id == current_user.id,
        BenefitEnrollment.benefit_id == enrollment.benefit_id,
        BenefitEnrollment.enrollment_status != "rejected"
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled in this benefit")
    
    db_enrollment = BenefitEnrollment(
        user_id=current_user.id,
        benefit_id=enrollment.benefit_id,
        enrollment_date=enrollment.enrollment_date
    )
    db.add(db_enrollment)
    db.commit()
    db.refresh(db_enrollment)
    return db_enrollment

@router.get("/benefits/enrollments", response_model=List[BenefitEnrollmentResponse])
async def get_my_enrollments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    enrollments = db.query(BenefitEnrollment).filter(
        BenefitEnrollment.user_id == current_user.id
    ).all()
    return enrollments

@router.get("/benefits/my-active-benefits", response_model=List[BenefitResponse])
async def get_my_active_benefits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all active benefits that the current user is enrolled in and eligible for their grade"""
    user_grade = str(current_user.grade)
    active_enrollments = db.query(BenefitEnrollment).filter(
        BenefitEnrollment.user_id == current_user.id,
        BenefitEnrollment.enrollment_status == "approved"
    ).all()
    benefit_ids = [enrollment.benefit_id for enrollment in active_enrollments]
    benefits = db.query(Benefit).filter(
        Benefit.benefit_id.in_(benefit_ids),
        Benefit.is_active == True,
        Benefit.grades.any(user_grade)
    ).all()
    return benefits

@router.get("/benefits/user-active-benefits/{user_id}", response_model=List[BenefitResponse])
async def get_user_active_benefits(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get active benefits for a specific user (manager only, can only view subordinates)"""
    # Verify manager permissions
    verify_manager_permission(db, current_user, user_id)
    # Get the target user and their grade
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    user_grade = str(target_user.grade)
    active_enrollments = db.query(BenefitEnrollment).filter(
        BenefitEnrollment.user_id == user_id,
        BenefitEnrollment.enrollment_status == "approved"
    ).all()
    benefit_ids = [enrollment.benefit_id for enrollment in active_enrollments]
    benefits = db.query(Benefit).filter(
        Benefit.benefit_id.in_(benefit_ids),
        Benefit.is_active == True,
        Benefit.grades.any(user_grade)
    ).all()
    return benefits

@router.put("/benefits/enrollments/{enrollment_id}/approve", response_model=BenefitEnrollmentResponse)
async def approve_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    enrollment = db.query(BenefitEnrollment).filter(BenefitEnrollment.enrollment_id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    # Verify manager permissions
    verify_manager_permission(db, current_user, enrollment.user_id)
    
    if enrollment.enrollment_status != "pending":
        raise HTTPException(status_code=400, detail="Enrollment is not in pending status")
    
    enrollment.enrollment_status = "approved"
    enrollment.approved_by = current_user.id
    enrollment.approved_at = datetime.now()
    
    db.commit()
    db.refresh(enrollment)
    return enrollment

@router.put("/benefits/enrollments/{enrollment_id}/reject", response_model=BenefitEnrollmentResponse)
async def reject_enrollment(
    enrollment_id: int,
    rejection: BenefitEnrollmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    enrollment = db.query(BenefitEnrollment).filter(BenefitEnrollment.enrollment_id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    # Verify manager permissions
    verify_manager_permission(db, current_user, enrollment.user_id)
    
    if enrollment.enrollment_status != "pending":
        raise HTTPException(status_code=400, detail="Enrollment is not in pending status")
    
    enrollment.enrollment_status = "rejected"
    enrollment.approved_by = current_user.id
    enrollment.approved_at = datetime.now()
    enrollment.rejection_reason = rejection.rejection_reason
    
    db.commit()
    db.refresh(enrollment)
    return enrollment 