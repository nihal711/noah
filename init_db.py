#!/usr/bin/env python3
"""
Database initialization script for Noah HR Management API
Creates sample users and leave balances for demo purposes.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from auth import get_password_hash

def init_database():
    """Initialize database with sample data"""
    
    # Create all tables
    models.Base.metadata.create_all(bind=engine)
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Check if users already exist
        existing_users = db.query(models.User).count()
        if existing_users > 0:
            print("Database already initialized with users.")
            return
        
        # Create sample users
        sample_users = [
            {
                "username": "nihal711",
                "email": "nihal@optioai.tech",
                "full_name": "Nihal Yusof   ",
                "employee_id": "EMP001",
                "department": "Engineering",
                "position": "Solutions Engineer",
                "password": "Optio#2024"
            }
            {
                "username": "jane_smith",
                "email": "jane.smith@noah.com",
                "full_name": "Jane Smith",
                "employee_id": "EMP002",
                "department": "Human Resources",
                "position": "HR Manager",
                "password": "password123"
            },
            {
                "username": "mike_johnson",
                "email": "mike.johnson@noah.com",
                "full_name": "Mike Johnson",
                "employee_id": "EMP003",
                "department": "Engineering",
                "position": "Team Lead",
                "password": "password123",
                "manager_id": None  # Will be set after creating users
            },
            {
                "username": "sarah_wilson",
                "email": "sarah.wilson@noah.com",
                "full_name": "Sarah Wilson",
                "employee_id": "EMP004",
                "department": "Marketing",
                "position": "Marketing Specialist",
                "password": "password123"
            }
        ]
        
        created_users = []
        
        # Create users
        for user_data in sample_users:
            password = user_data.pop("password")
            hashed_password = get_password_hash(password)
            
            user = models.User(
                **user_data,
                hashed_password=hashed_password
            )
            
            db.add(user)
            db.flush()  # Flush to get the ID
            created_users.append(user)
        
        # Set manager relationships
        created_users[0].manager_id = created_users[2].id  # John reports to Mike
        created_users[3].manager_id = created_users[2].id  # Sarah reports to Mike
        
        # Create leave balances for all users
        leave_types = ["Annual", "Sick", "Personal"]
        current_year = datetime.now().year
        
        for user in created_users:
            for leave_type in leave_types:
                if leave_type == "Annual":
                    total_days = 25.0
                elif leave_type == "Sick":
                    total_days = 10.0
                else:  # Personal
                    total_days = 5.0
                
                leave_balance = models.LeaveBalance(
                    user_id=user.id,
                    leave_type=leave_type,
                    total_days=total_days,
                    used_days=0.0,
                    remaining_days=total_days,
                    year=current_year
                )
                db.add(leave_balance)
        
        # Commit all changes
        db.commit()
        
        print("Database initialized successfully!")
        print("\nSample users created:")
        for user in created_users:
            print(f"- {user.username} ({user.full_name}) - {user.department}")
        
        print("\nDefault password for all users: password123")
        print("\nLeave balances created:")
        print("- Annual: 25 days")
        print("- Sick: 10 days") 
        print("- Personal: 5 days")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()