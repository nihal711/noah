#!/usr/bin/env python3
"""
Database initialization script for Salary and Benefits tables
Creates tables and adds sample data for existing users.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from auth import get_current_active_user

def init_salary_benefits():
    """Initialize salary and benefits tables with sample data"""
    
    print("Creating salary and benefits tables...")
    # Create tables
    models.Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Check if benefits already exist
        existing_benefits = db.query(models.Benefit).count()
        if existing_benefits > 0:
            print("Benefits already initialized.")
            return
        
        print("\nInitializing sample data...")
        
        # Create sample benefits
        sample_benefits = [
            {
                "benefit_name": "Health Insurance",
                "benefit_description": "Comprehensive health insurance coverage",
                "benefit_type": "health_insurance",
                "max_amount": 10000.0,
                "is_active": True
            },
            {
                "benefit_name": "Life Insurance",
                "benefit_description": "Life insurance coverage",
                "benefit_type": "life_insurance",
                "max_amount": 500000.0,
                "is_active": True
            },
            {
                "benefit_name": "Dental Coverage",
                "benefit_description": "Dental insurance coverage",
                "benefit_type": "dental_insurance",
                "max_amount": 2000.0,
                "is_active": True
            },
            {
                "benefit_name": "Gym Membership",
                "benefit_description": "Annual gym membership reimbursement",
                "benefit_type": "wellness",
                "max_amount": 500.0,
                "is_active": True
            }
        ]
        
        created_benefits = []
        for benefit_data in sample_benefits:
            benefit = models.Benefit(**benefit_data)
            db.add(benefit)
            db.flush()
            created_benefits.append(benefit)
        
        # Get all existing users
        existing_users = db.query(models.User).all()
        print(f"\nFound {len(existing_users)} existing users")
        
        # Create sample salary structures for existing users
        for user in existing_users:
            # Check if user already has a salary structure
            existing_salary = db.query(models.SalaryStructure).filter(
                models.SalaryStructure.user_id == user.id
            ).first()
            
            if not existing_salary:
                salary_structure = models.SalaryStructure(
                    user_id=user.id,
                    basic_salary=5000.0,
                    allowances={
                        "HRA": 2000.0,
                        "Transport": 1000.0,
                        "Meal": 500.0
                    },
                    deductions={
                        "Tax": 500.0,
                        "PF": 600.0
                    },
                    effective_date=datetime.now()
                )
                db.add(salary_structure)
        
        # Create sample benefit enrollments
        for user in existing_users:
            # Enroll in health insurance
            enrollment = models.BenefitEnrollment(
                user_id=user.id,
                benefit_id=created_benefits[0].benefit_id,  # Health Insurance
                enrollment_status="approved",
                enrollment_date=datetime.now(),
                approved_by=user.id,  # Self-approved for sample data
                approved_at=datetime.now()
            )
            db.add(enrollment)
            
            # Enroll in gym membership (pending)
            enrollment = models.BenefitEnrollment(
                user_id=user.id,
                benefit_id=created_benefits[3].benefit_id,  # Gym Membership
                enrollment_status="pending",
                enrollment_date=datetime.now()
            )
            db.add(enrollment)
        
        # Commit all changes
        db.commit()
        
        print("\nInitialization completed successfully!")
        print("\nBenefits created:")
        for benefit in created_benefits:
            print(f"- {benefit.benefit_name}: ${benefit.max_amount}")
        
        print("\nSalary structures created for existing users")
        print("Sample benefit enrollments created")
        
        print("\nYou can now use the following APIs:")
        print("1. Salary Structure APIs:")
        print("   - POST /salary/structure - Create salary structure")
        print("   - GET /salary/structure - Get own salary structure")
        print("   - GET /salary/structure/{user_id} - Get user's salary structure (manager only)")
        print("   - PUT /salary/structure/{user_id} - Update salary structure (manager only)")
        print("\n2. Benefits APIs:")
        print("   - GET /benefits - List available benefits")
        print("   - POST /benefits/enroll - Enroll in a benefit")
        print("   - GET /benefits/enrollments - View own enrollments")
        print("   - PUT /benefits/enrollments/{enrollment_id}/approve - Approve enrollment (manager only)")
        print("   - PUT /benefits/enrollments/{enrollment_id}/reject - Reject enrollment (manager only)")
        
    except Exception as e:
        print(f"\nError during initialization: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_salary_benefits() 