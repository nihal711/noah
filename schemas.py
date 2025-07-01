from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date
from typing import Optional, List
from models import CourseCategory
from enum import Enum as PyEnum




class DepartmentEnum(PyEnum):
    ENGINEERING = "Engineering"
    HR = "Human Resources"
    MARKETING = "Marketing"
    FINANCE = "Finance"

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    employee_id: str
    department: DepartmentEnum
    position: str
    manager_id: Optional[int] = None
    grade: Optional[str] = None
    doj: Optional[datetime] = None
    linemanager: Optional[str] = None
    workphone: Optional[str] = None
    mobilephone: Optional[str] = None
    bankname: Optional[str] = None
    branchname: Optional[str] = None
    gender: str
    sbu: Optional[str] = None
    religion: str = "Not Specified"
    categories: Optional[List[str]] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Authentication Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str


# Leave Request Schemas
class LeaveRequestBase(BaseModel):
    leave_type: str
    start_date: date
    end_date: date
    days_requested: float
    reason: str

class LeaveRequestCreate(LeaveRequestBase):
    pass

class LeaveRequestResponse(LeaveRequestBase):
    id: int
    user_id: int
    status: str
    approver_comments: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class LeaveRequestWithEmployeeResponse(LeaveRequestResponse):
    employee_name: Optional[str] = None
    employee_email: Optional[str] = None
    

class LeaveRequestUpdate(BaseModel):
    status: str
    approver_comments: Optional[str] = None

# Leave Balance Schemas
class LeaveBalanceBase(BaseModel):
    leave_type: str
    total_days: float
    used_days: float
    remaining_days: float
    year: int

class LeaveBalanceCreate(LeaveBalanceBase):
    user_id: int

class LeaveBalanceResponse(LeaveBalanceBase):
    id: int
    user_id: int
    
    class Config:
        from_attributes = True

# Attachment Schemas
class AttachmentBase(BaseModel):
    fileName: str
    fileType: str
    fileDesc: Optional[str] = None
    fileData: str

class AttachmentCreate(AttachmentBase):
    pass

class AttachmentResponse(BaseModel):
    id: int
    file_name: str
    file_type: str
    file_desc: Optional[str] = None
    file_data: str
    
    class Config:
        from_attributes = True

# Bank Letter Request Schemas
class BankLetterRequestBase(BaseModel):
    type: str
    comment: Optional[str] = None
    language: str = "English"
    addressedTo: str
    bankName: str
    branchName: str

class BankLetterRequestCreate(BankLetterRequestBase):
    attachments: List[AttachmentCreate] = []

class BankLetterRequestResponse(BaseModel):
    id: int
    user_id: int
    bank_name: str
    comment: Optional[str] = None
    status: str
    approver_comments: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    attachments: List[AttachmentResponse] = []
    
    class Config:
        from_attributes = True

class BankLetterRequestUpdate(BaseModel):
    status: str
    approver_comments: Optional[str] = None

# Visa Letter Request Schemas
class VisaLetterRequestBase(BaseModel):
    type: str
    comment: Optional[str] = None
    language: str = "English"
    addressedTo: str
    country: str

class VisaLetterRequestCreate(VisaLetterRequestBase):
    attachments: List[AttachmentCreate] = []

class VisaLetterRequestResponse(BaseModel):
    id: int
    user_id: int
    type: str
    comment: Optional[str] = None
    language: str
    addressed_to: str
    country: str
    status: str
    approver_comments: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    attachments: List[AttachmentResponse] = []
    
    class Config:
        from_attributes = True

class VisaLetterRequestUpdate(BaseModel):
    status: str
    approver_comments: Optional[str] = None

# Generic Response Schemas
class MessageResponse(BaseModel):
    message: str

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

# Combined Requests View Schema
class RequestSummary(BaseModel):
    id: int
    type: str
    request_type: str  # "leave", "bank_letter", "visa_letter"
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: int
    user_full_name: str
    user_email: str
    details: Optional[str] = None
    
    class Config:
        from_attributes = True

class PayslipBase(BaseModel):
    month: int
    year: int
    basic_salary: float
    allowances: float
    deductions: float
    net_salary: float

class PayslipCreate(PayslipBase):
    pass

class PayslipUpdate(BaseModel):
    basic_salary: Optional[float] = None
    allowances: Optional[float] = None
    deductions: Optional[float] = None
    net_salary: Optional[float] = None

class PayslipResponse(PayslipBase):
    payslip_id: int
    user_id: int
    status: str
    approver_comments: Optional[str] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    approver_comments: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Salary Structure Schemas
class SalaryStructureBase(BaseModel):
    basic_salary: float
    allowances: dict
    deductions: dict
    effective_date: datetime

class SalaryStructureCreate(SalaryStructureBase):
    pass

class SalaryStructureUpdate(SalaryStructureBase):
    pass

class SalaryStructureResponse(SalaryStructureBase):
    id: int
    user_id: int
    
    class Config:
        from_attributes = True

# Benefit Schemas
class BenefitBase(BaseModel):
    benefit_name: str
    benefit_description: str
    benefit_type: str
    max_amount: float
    is_active: bool = True

class BenefitCreate(BenefitBase):
    pass

class BenefitResponse(BenefitBase):
    benefit_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Benefit Enrollment Schemas
class BenefitEnrollmentBase(BaseModel):
    benefit_id: int
    enrollment_date: datetime

class BenefitEnrollmentCreate(BenefitEnrollmentBase):
    pass

class BenefitEnrollmentResponse(BenefitEnrollmentBase):
    enrollment_id: int
    user_id: int
    enrollment_status: str
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    benefit: BenefitResponse
    
    class Config:
        from_attributes = True

class BenefitEnrollmentUpdate(BaseModel):
    rejection_reason: Optional[str] = None

# Goal Schemas
class GoalBase(BaseModel):
    title: str
    description: str
    target_date: datetime
    year: int
    progress:int
    goal_for: str  # self or subordinate
    user_id: Optional[int] = None

class GoalCreate(GoalBase):
    pass

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    target_date: Optional[datetime] = None

class GoalResponse(GoalBase):
    goal_id: int
    user_id: int

    class Config:
        from_attributes = True

class UserGoalsResponse(BaseModel):
    user_id: int
    username: str
    full_name: str
    goals: List[GoalResponse]

class ReviewBase(BaseModel):
    user_id: int
    goal_id: int
    overall_rating: int
    comments: str  # Employee's self-review

class ReviewCreate(BaseModel):
    goal_id: int = Field(..., description="ID of the goal being reviewed")
    achievements: str = Field(..., description="Employee's summary of accomplishments.")
    rating_quality: int = Field(..., ge=1, le=5, description="Rating for quality of work (1-5).")
    rating_productivity: int = Field(..., ge=1, le=5, description="Rating for productivity (1-5).")
    rating_communication: int = Field(..., ge=1, le=5, description="Rating for communication (1-5).")
    overall_rating: int = Field(..., ge=1, le=5, description="Overall self-rating for the goal (1-5)")

class ReviewResponse(BaseModel):
    review_id: int
    user_id: int
    goal_id: int
    year: int
    overall_rating: Optional[int] = Field(None, ge=1, le=5)
    achievements: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    rating_quality: Optional[int] = Field(None, ge=1, le=5)
    rating_productivity: Optional[int] = Field(None, ge=1, le=5)
    rating_communication: Optional[int] = Field(None, ge=1, le=5)
    status: str
    approver_rating_overall: Optional[int] = Field(None, ge=1, le=5)
    approver_comments: Optional[str] = None  # Manager/approver's comments
    goal: "PerformanceGoal"

    class Config:
        from_attributes = True

class ManagerReview(BaseModel):
    approver_rating_overall: int = Field(
        ...,
        ge=1,
        le=5,
        description="Manager's rating for the review (1-5)"
    )
    approver_comments: str = Field(..., description="Manager's review comments")
    areas_for_improvement: str = Field(..., description="Manager's feedback on where to grow.")

class ReviewRejection(BaseModel):
    approver_comments: str = Field(..., description="Reason for rejecting the review")

class ReviewStatusResponse(BaseModel):
    goal_title: str
    review_status: str
    overall_rating: Optional[int] = Field(None, ge=1, le=5)
    approver_rating_overall: Optional[int] = Field(None, ge=1, le=5)
    approver_comments: Optional[str] = None

    class Config:
        from_attributes = True

class ReviewReportDetail(BaseModel):
    review_id: int
    user_id: int
    goal_id: int
    year: int
    overall_rating: Optional[int] = Field(None, ge=1, le=5)
    achievements: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    rating_quality: Optional[int] = Field(None, ge=1, le=5)
    rating_productivity: Optional[int] = Field(None, ge=1, le=5)
    rating_communication: Optional[int] = Field(None, ge=1, le=5)
    status: str
    approver_rating_overall: Optional[int] = Field(None, ge=1, le=5)
    approver_comments: Optional[str] = None

    class Config:
        from_attributes = True

class GoalReviewReportItem(BaseModel):
    goal: "PerformanceGoal"
    review: Optional[ReviewReportDetail] = None

class PerformanceGoalBase(BaseModel):
    title: str = Field(..., description="Title of the performance goal")
    description: str = Field(..., description="Detailed description of the goal")
    target_date: datetime = Field(..., description="Target completion date for the goal")
    year: int = Field(..., description="Year for which the goal is set")
    goal_for: str = Field(..., description="Type of goal: 'self' or 'subordinate'")
    progress: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Progress percentage of the goal (0-100)"
    )

class PerformanceGoalCreate(PerformanceGoalBase):
    user_id: Optional[int] = Field(None, description="ID of the subordinate user (required only for subordinate goals)")

class PerformanceGoalUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Title of the performance goal")
    description: Optional[str] = Field(None, description="Detailed description of the goal")
    target_date: Optional[datetime] = Field(None, description="Target completion date for the goal")
    progress: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Progress percentage of the goal (0-100)"
    )

class PerformanceGoal(PerformanceGoalBase):
    goal_id: int
    user_id: int

    class Config:
        from_attributes = True

class CourseBase(BaseModel):
    title: str
    description: str
    category: CourseCategory
    instructor: str
    start_date: date
    end_date: date
    duration: int

class CourseCreate(CourseBase):
    pass

class CourseResponse(CourseBase):
    course_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool
    duration_str: Optional[str] = None
    department_categories: Optional[List[str]] = None

    class Config:
        from_attributes = True
        use_enum_values = True

class DepartmentCoursesResponse(BaseModel):
    categories: List[str]
    courses: List[CourseResponse]

    class Config:
        use_enum_values = True

class EnrollmentBase(BaseModel):
    course_id: int

class EnrollmentCreate(EnrollmentBase):
    pass

class EnrollmentResponse(EnrollmentBase):
    enrollment_id: int
    user_id: int
    enrolled_at: datetime
    status: str
    progress: int
    course: Optional[CourseResponse] = None

    class Config:
        from_attributes = True

class CompletionBase(BaseModel):
    course_id: int

class CompletionCreate(CompletionBase):
    pass

class CompletionResponse(CompletionBase):
    completion_id: int
    user_id: int
    completed_at: datetime
    certificate_url: Optional[str]
    course: Optional[CourseResponse] = None

    class Config:
        from_attributes = True

# Filter Schemas
class CourseFilter(BaseModel):
    category: Optional[CourseCategory] = None
    instructor: Optional[str] = None
    is_active: Optional[bool] = None

class EnrollmentFilter(BaseModel):
    year: Optional[int] = None
    status: Optional[str] = None
    course_id: Optional[int] = None

class CompletionFilter(BaseModel):
    year: Optional[int] = None
    course_id: Optional[int] = None

# Overtime Request Schemas
class OvertimeRequestBase(BaseModel):
    date: date
    hours: float
    reason: Optional[str] = None

class OvertimeRequestCreate(OvertimeRequestBase):
    attachment: Optional[AttachmentCreate] = None

class OvertimeRequestPartialUpdate(BaseModel):
    date: Optional[date] = None
    hours: Optional[float] = None
    reason: Optional[str] = None
    class Config:
        from_attributes = True

class OvertimeRequestUpdate(BaseModel):
    date: date
    hours: float
    reason: Optional[str] = None
    class Config:
        from_attributes = True

class OvertimeRequestResponse(OvertimeRequestBase):
    id: int
    user_id: int
    status: str
    approver_comments: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    leave_days_granted: Optional[float] = None
    message: Optional[str] = None
    class Config:
        from_attributes = True

class OvertimePreviewResponse(BaseModel):
    entitled_hours: float
    entitled_leave_days: float
    capped: bool
    message: str

class OvertimeRequestApproval(BaseModel):
    approver_comments: Optional[str] = None

class OvertimeRequestRejection(BaseModel):
    approver_comments: str

class UserOvertimeRequests(BaseModel):
    user_id: int
    username: str
    full_name: str
    requests: List[OvertimeRequestResponse]

    class Config:
        from_attributes = True

ReviewResponse.model_rebuild()
GoalReviewReportItem.model_rebuild() 