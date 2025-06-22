from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, UniqueConstraint, JSON, Date, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    employee_id = Column(String, unique=True, nullable=False)
    department = Column(String, nullable=False)
    position = Column(String, nullable=False)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    grade = Column(String(100))
    doj = Column(DateTime)
    linemanager = Column(String(1000))
    workphone = Column(String(100))
    mobilephone = Column(String(200))
    bankname = Column(String(4000))
    branchname = Column(String(4000))
    
    # Essential relationships
    leave_requests = relationship("LeaveRequest", back_populates="user")
    bank_letter_requests = relationship("BankLetterRequest", back_populates="user")
    visa_letter_requests = relationship("VisaLetterRequest", back_populates="user")
    payslips = relationship("Payslip", back_populates="user", foreign_keys="Payslip.user_id")
    salary_structure = relationship("SalaryStructure", back_populates="user", foreign_keys="SalaryStructure.user_id", uselist=False)
    benefit_enrollments = relationship("BenefitEnrollment", back_populates="user", foreign_keys="BenefitEnrollment.user_id")
    
    performance_goals = relationship("PerformanceGoal", back_populates="user", foreign_keys="PerformanceGoal.user_id")
    performance_reviews = relationship("PerformanceReview", back_populates="user", foreign_keys="PerformanceReview.user_id")
    overtime_requests = relationship("OvertimeRequest", back_populates="user")

class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    leave_type = Column(String, nullable=False)  # annual, sick, personal, etc.
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    days_requested = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String, default="pending")  # pending, approved, rejected
    approver_comments = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="leave_requests")

class LeaveBalance(Base):
    __tablename__ = "leave_balances"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    leave_type = Column(String, nullable=False)
    total_days = Column(Float, nullable=False)
    used_days = Column(Float, default=0.0)
    remaining_days = Column(Float, nullable=False)
    year = Column(Integer, nullable=False)
    
    # Relationships
    user = relationship("User")

class Attachment(Base):
    __tablename__ = "attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_desc = Column(String, nullable=True)
    file_data = Column(Text, nullable=False)  # Base64 encoded file data
    bank_letter_request_id = Column(Integer, ForeignKey("bank_letter_requests.id"), nullable=True)
    visa_letter_request_id = Column(Integer, ForeignKey("visa_letter_requests.id"), nullable=True)

class BankLetterRequest(Base):
    __tablename__ = "bank_letter_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bank_name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    additional_details = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, approved, rejected, completed
    approver_comments = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="bank_letter_requests")
    attachments = relationship("Attachment", foreign_keys=[Attachment.bank_letter_request_id])

class VisaLetterRequest(Base):
    __tablename__ = "visa_letter_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)  # employment letter, salary certificate, etc.
    comment = Column(Text, nullable=True)
    language = Column(String, nullable=False, default="English")
    addressed_to = Column(String, nullable=False)
    country = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, approved, rejected, completed
    approver_comments = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="visa_letter_requests")
    attachments = relationship("Attachment", foreign_keys=[Attachment.visa_letter_request_id]) 

class Payslip(Base):
    __tablename__ = "payslips"
    
    payslip_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)
    basic_salary = Column(Float, nullable=False)
    allowances = Column(Float, default=0.0)
    deductions = Column(Float, default=0.0)
    net_salary = Column(Float, nullable=False)
    status = Column(String, default="pending")  # pending, approved, rejected
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approver_comments = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('user_id', 'month', 'year', name='uix_user_month_year'),
    )
    
    # Essential relationships for payslip functionality
    user = relationship("User", foreign_keys=[user_id], back_populates="payslips")
    approver = relationship("User", foreign_keys=[approved_by])
User.payslips = relationship("Payslip", back_populates="user", foreign_keys=[Payslip.user_id]) 

class SalaryStructure(Base):
    __tablename__ = "salary_structures"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    basic_salary = Column(Float, nullable=False)
    allowances = Column(JSON, nullable=False, default={})
    deductions = Column(JSON, nullable=False, default={})
    effective_date = Column(DateTime(timezone=True), nullable=False)
    
    # Essential relationship
    user = relationship("User", foreign_keys=[user_id], back_populates="salary_structure")

class Benefit(Base):
    __tablename__ = "benefits"
    
    benefit_id = Column(Integer, primary_key=True, index=True)
    benefit_name = Column(String, nullable=False)
    benefit_description = Column(Text, nullable=False)
    benefit_type = Column(String, nullable=False)  # health_insurance, life_insurance, etc.
    max_amount = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class BenefitEnrollment(Base):
    __tablename__ = "benefit_enrollments"
    
    enrollment_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    benefit_id = Column(Integer, ForeignKey("benefits.benefit_id"), nullable=False)
    enrollment_status = Column(String, default="pending")  # pending, approved, rejected
    enrollment_date = Column(DateTime(timezone=True), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Essential relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="benefit_enrollments")
    benefit = relationship("Benefit")
    approver = relationship("User", foreign_keys=[approved_by]) 


class PerformanceGoal(Base):
    __tablename__ = "performance_goals"
    
    goal_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    target_date = Column(DateTime(timezone=True), nullable=False)
    year = Column(Integer, nullable=False)
    goal_for = Column(String, nullable=False)  # self or subordinate
    progress = Column(Integer, default=0)  # 0-100 percentage
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="performance_goals")
    reviews = relationship("PerformanceReview", back_populates="goal")

class PerformanceReview(Base):
    __tablename__ = "performance_reviews"
    
    review_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    goal_id = Column(Integer, ForeignKey("performance_goals.goal_id"), nullable=False)
    year = Column(Integer, nullable=False)
    overall_rating = Column(Integer, nullable=True)
    achievements = Column(Text, nullable=True)
    areas_for_improvement = Column(Text, nullable=True)
    rating_quality = Column(Integer, nullable=True)
    rating_productivity = Column(Integer, nullable=True)
    rating_communication = Column(Integer, nullable=True)
    status = Column(String, default="pending")  # pending, approved, rejected
    approver_rating_overall = Column(Integer, nullable=True)
    approver_comments = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="performance_reviews")
    goal = relationship("PerformanceGoal", back_populates="reviews")

class Course(Base):
    __tablename__ = "courses"
    
    course_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String, nullable=False)
    instructor = Column(String, nullable=False)
    duration = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    enrollments = relationship("Enrollment", back_populates="course")
    completions = relationship("Completion", back_populates="course")

class Enrollment(Base):
    __tablename__ = "enrollments"
    
    enrollment_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.course_id"), nullable=False)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, nullable=False)  # 'active', 'completed', 'dropped'
    progress = Column(Integer, default=0)

    # Relationships
    user = relationship("User")
    course = relationship("Course", back_populates="enrollments")

class Completion(Base):
    __tablename__ = "completions"
    
    completion_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.course_id"), nullable=False)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    certificate_url = Column(String)

    # Relationships
    user = relationship("User")
    course = relationship("Course", back_populates="completions") 

class OvertimeRequest(Base):
    __tablename__ = "overtime_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    hours = Column(Float, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, approved, rejected
    approver_comments = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    attachment_id = Column(Integer, ForeignKey("attachments.id"), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="overtime_requests")
    attachment = relationship("Attachment")


class OvertimeLeave(Base):
    __tablename__ = "overtime_leaves"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    overtime_request_id = Column(Integer, ForeignKey("overtime_requests.id"), nullable=False)
    year = Column(Integer, nullable=False)
    ot_hours = Column(Float, nullable=False)
    leave_days = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")
    overtime_request = relationship("OvertimeRequest") 