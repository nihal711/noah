from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
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
    
    # Relationships
    leave_requests = relationship("LeaveRequest", back_populates="user")
    bank_letter_requests = relationship("BankLetterRequest", back_populates="user")
    visa_letter_requests = relationship("VisaLetterRequest", back_populates="user")

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
    manager_comments = Column(Text, nullable=True)
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
    purpose = Column(String, nullable=False)
    additional_details = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, approved, rejected, completed
    hr_comments = Column(Text, nullable=True)
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
    hr_comments = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="visa_letter_requests")
    attachments = relationship("Attachment", foreign_keys=[Attachment.visa_letter_request_id]) 