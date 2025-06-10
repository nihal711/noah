#!/usr/bin/env python3
"""
Database initialization script for Payslip data
Creates sample payslips for existing users.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

def init_payslips():
    """Initialize database with sample payslip data"""
    
    # Create the payslips table if it doesn't exist
    models.Base.metadata.create_all(bind=engine)
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Check if payslips already exist
        existing_payslips = db.query(models.Payslip).count()
        if existing_payslips > 0:
            print("Payslips already exist in the database.")
            return
        
        # Get all existing users
        users = db.query(models.User).all()
        if not users:
            print("No users found in the database. Please create users first.")
            return
        
        # Create sample payslips for the last 3 months
        current_date = datetime.now()
        current_month = current_date.month
        current_year = current_date.year
        
        # Sample salary configurations for different positions
        salary_configs = {
            "Solutions Engineer": {"basic": 5000.0, "allowances": 1000.0},
            "HR Manager": {"basic": 6000.0, "allowances": 1200.0},
            "Team Lead": {"basic": 7000.0, "allowances": 1400.0},
            "Marketing Specialist": {"basic": 4500.0, "allowances": 900.0},
            # Default configuration for any other positions
            "default": {"basic": 4000.0, "allowances": 800.0}
        }
        
        # Create payslips for each user for the last 3 months
        for user in users:
            # Get salary config based on position, use default if position not found
            salary_config = salary_configs.get(user.position, salary_configs["default"])
            basic_salary = salary_config["basic"]
            allowances = salary_config["allowances"]
            
            for i in range(3):
                month = current_month - i
                year = current_year
                
                if month <= 0:
                    month += 12
                    year -= 1
                
                # Calculate deductions (example: 10% of basic salary)
                deductions = basic_salary * 0.1
                net_salary = basic_salary + allowances - deductions
                
                # Create payslip
                payslip = models.Payslip(
                    user_id=user.id,
                    month=month,
                    year=year,
                    basic_salary=basic_salary,
                    allowances=allowances,
                    deductions=deductions,
                    net_salary=net_salary,
                    status="approved" if i > 0 else "pending"  # Older payslips are approved
                )
                db.add(payslip)
        
        # Commit all changes
        db.commit()
        
        print("Payslips initialized successfully!")
        print("\nCreated payslips for the following users:")
        for user in users:
            print(f"- {user.username} ({user.full_name}) - {user.position}")
        
        print("\nPayslip details:")
        print("- Last 3 months of payslips for each user")
        print("- Different salary configurations based on position")
        print("- Older payslips marked as approved")
        print("- Current month's payslip marked as pending")
        
    except Exception as e:
        print(f"Error initializing payslips: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_payslips() 