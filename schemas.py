from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    employee_id: str
    department: str
    position: str
    manager_id: Optional[int] = None

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
    start_date: datetime
    end_date: datetime
    days_requested: float
    reason: str

class LeaveRequestCreate(LeaveRequestBase):
    pass

class LeaveRequestResponse(LeaveRequestBase):
    id: int
    user_id: int
    status: str
    manager_comments: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class LeaveRequestUpdate(BaseModel):
    status: str
    manager_comments: Optional[str] = None

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
    purpose: str
    additional_details: Optional[str] = None
    status: str
    hr_comments: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    attachments: List[AttachmentResponse] = []
    
    class Config:
        from_attributes = True

class BankLetterRequestUpdate(BaseModel):
    status: str
    hr_comments: Optional[str] = None

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
    hr_comments: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    attachments: List[AttachmentResponse] = []
    
    class Config:
        from_attributes = True

class VisaLetterRequestUpdate(BaseModel):
    status: str
    hr_comments: Optional[str] = None

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
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

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