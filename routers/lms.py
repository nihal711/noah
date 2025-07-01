from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import extract
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import Course, Enrollment, Completion, User
from schemas import (
    CourseCreate,
    CourseResponse,
    EnrollmentCreate,
    EnrollmentResponse,
    CompletionCreate,
    CompletionResponse,
    CourseFilter,
    EnrollmentFilter,
    CompletionFilter,
    DepartmentCoursesResponse
)
from auth import get_current_active_user, get_current_user

router = APIRouter()

DEPT_CATEGORY_MAP = {
    "ENGINEERING": ["TECH", "HR"],
    "MARKETING": ["MARKETING", "HR"],
    "FINANCE": ["FINANCE", "HR"],
    "HUMAN_RESOURCES": ["HR"],
}

# Course endpoints
@router.post("/courses", response_model=CourseResponse)
def create_course(
    *,
    db: Session = Depends(get_db),
    course_in: CourseCreate,
    current_user = Depends(get_current_user)
):
    """
    Create a new course.
    """
    db_course = Course(**course_in.model_dump())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@router.get("/courses", response_model=DepartmentCoursesResponse)
def get_courses(
    *,
    db: Session = Depends(get_db),
    category: Optional[str] = None,
    instructor: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all courses with optional filtering, filtered by department categories.
    """
    allowed_categories = DEPT_CATEGORY_MAP.get(current_user.department.value, ["HR"])
    query = db.query(Course).filter(Course.category.in_(allowed_categories))
    if category:
        query = query.filter(Course.category == category)
    if instructor:
        query = query.filter(Course.instructor == instructor)
    if is_active is not None:
        query = query.filter(Course.is_active == is_active)
    courses = query.all()
    course_responses = [CourseResponse.from_orm(course) for course in courses]
    for course_response in course_responses:
        course_response.department_categories = allowed_categories
    return DepartmentCoursesResponse(categories=allowed_categories, courses=course_responses)

@router.get("/courses/{course_id}", response_model=CourseResponse)
def get_course(
    *,
    db: Session = Depends(get_db),
    course_id: int,
    current_user = Depends(get_current_user)
):
    """
    Get a specific course by ID.
    """
    course = db.query(Course).filter(Course.course_id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.get("/courses/upcoming", response_model=DepartmentCoursesResponse)
def get_upcoming_courses(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all upcoming (future) active courses, sorted by start_date ascending, filtered by department categories.
    """
    today = datetime.utcnow().date()
    allowed_categories = DEPT_CATEGORY_MAP.get(current_user.department, ["HR"])
    courses = db.query(Course).filter(
        Course.is_active == True,
        Course.start_date > today,
        Course.category.in_(allowed_categories)
    ).order_by(Course.start_date.asc()).all()
    course_responses = [CourseResponse.from_orm(course) for course in courses]
    for course_response in course_responses:
        course_response.department_categories = allowed_categories
    return DepartmentCoursesResponse(categories=allowed_categories, courses=course_responses)

@router.get("/courses/all", response_model=List[CourseResponse])
def get_all_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all courses (admin/manager view, no department/category filtering).
    """
    return db.query(Course).all()

@router.get("/courses/available", response_model=DepartmentCoursesResponse)
def get_available_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all courses available to the current user (filtered by department/category).
    """
    allowed_categories = DEPT_CATEGORY_MAP.get(current_user.department, ["HR"])
    courses = db.query(Course).filter(Course.category.in_(allowed_categories)).all()
    course_responses = [CourseResponse.from_orm(course) for course in courses]
    for course_response in course_responses:
        course_response.department_categories = allowed_categories
    return DepartmentCoursesResponse(categories=allowed_categories, courses=course_responses)

# Enrollment endpoints
@router.post("/enrollments", response_model=EnrollmentResponse)
def create_enrollment(
    *,
    db: Session = Depends(get_db),
    enrollment_in: EnrollmentCreate,
    current_user = Depends(get_current_user)
):
    """
    Enroll in a course.
    """
    # Check if course exists
    course = db.query(Course).filter(Course.course_id == enrollment_in.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    today = datetime.utcnow().date()
    # Only allow enrollment for ongoing or upcoming courses
    if course.end_date < today:
        raise HTTPException(status_code=400, detail="Cannot enroll in a course that has already ended.")
    # Check if already enrolled
    existing_enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == current_user.id,
        Enrollment.course_id == enrollment_in.course_id
    ).first()
    if existing_enrollment:
        raise HTTPException(status_code=400, detail="Already enrolled in this course")
    
    db_enrollment = Enrollment(
        user_id=current_user.id,
        **enrollment_in.model_dump(),
        status='active',
        progress=0
    )
    db.add(db_enrollment)
    db.commit()
    db.refresh(db_enrollment)
    return db_enrollment

@router.get("/enrollments", response_model=List[EnrollmentResponse])
def get_enrollments(
    *,
    db: Session = Depends(get_db),
    year: Optional[int] = None,
    status: Optional[str] = None,
    course_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user)
):
    """
    Get user's enrollments with optional filtering.
    """
    query = db.query(Enrollment).filter(Enrollment.user_id == current_user.id)
    
    if year:
        query = query.filter(extract('year', Enrollment.enrolled_at) == year)
    if status:
        query = query.filter(Enrollment.status == status)
    if course_id:
        query = query.filter(Enrollment.course_id == course_id)
    
    return query.offset(skip).limit(limit).all()

# Completion endpoints
@router.post("/completions", response_model=CompletionResponse)
def create_completion(
    *,
    db: Session = Depends(get_db),
    completion_in: CompletionCreate,
    current_user = Depends(get_current_user)
):
    """
    Mark a course as completed.
    """
    # Check if course exists
    course = db.query(Course).filter(Course.course_id == completion_in.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    today = datetime.utcnow().date()
    # Only allow completion if course has started
    if course.start_date > today:
        raise HTTPException(status_code=400, detail="Cannot complete a course that has not started yet.")
    # Check if enrolled
    enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == current_user.id,
        Enrollment.course_id == completion_in.course_id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=400, detail="Not enrolled in this course")
    # Check if already completed
    existing_completion = db.query(Completion).filter(
        Completion.user_id == current_user.id,
        Completion.course_id == completion_in.course_id
    ).first()
    if existing_completion:
        raise HTTPException(status_code=400, detail="Course already completed")
    # Create completion record
    db_completion = Completion(
        user_id=current_user.id,
        **completion_in.model_dump()
    )
    db.add(db_completion)
    # Update enrollment status
    enrollment.status = 'completed'
    enrollment.progress = 100
    db.commit()
    db.refresh(db_completion)
    return db_completion

@router.get("/completions", response_model=List[CompletionResponse])
def get_completions(
    *,
    db: Session = Depends(get_db),
    year: Optional[int] = None,
    course_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user)
):
    """
    Get user's completed courses with optional filtering.
    """
    query = db.query(Completion).filter(Completion.user_id == current_user.id)
    
    if year:
        query = query.filter(extract('year', Completion.completed_at) == year)
    if course_id:
        query = query.filter(Completion.course_id == course_id)
    
    return query.offset(skip).limit(limit).all() 