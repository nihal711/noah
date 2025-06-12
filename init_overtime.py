#!/usr/bin/env python3
"""
Database initialization script for Overtime Requests
Creates sample overtime requests for existing users.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
import random

def init_overtime_requests():
    """Initialize database with sample overtime request data"""
    
    # Create the overtime_requests table if it doesn't exist
    models.Base.metadata.create_all(bind=engine)
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Check if overtime requests already exist
        # existing_requests = db.query(models.OvertimeRequest).count()
        # if existing_requests > 0:
        #     print("Overtime requests already exist in the database.")
        #     return
        
        # # Get all existing users
        users = db.query(models.User).all()
        if not users:
            print("No users found in the database. Please create users first.")
            return
        
        # Sample reasons for overtime
        reasons = [
            "Project deadline",
            "System deployment",
            "Client meeting",
            "Emergency support",
            "Code review",
            "Documentation",
            "Training session",
            "Team building"
        ]
        
        # Create sample overtime requests for the last 3 months
        current_date = datetime.now()
        
        for user in users:
            # Create 2-4 random overtime requests per user
            num_requests = random.randint(2, 4)
            
            for _ in range(num_requests):
                # Random date within last 3 months
                random_days = random.randint(0, 90)
                request_date = current_date - timedelta(days=random_days)
                
                # Random hours between 1 and 8
                hours = random.randint(1, 8)
                
                # Random status (70% pending, 20% approved, 10% rejected)
                status_roll = random.random()
                if status_roll < 0.7:
                    status = "pending"
                    manager_comments = None
                elif status_roll < 0.9:
                    status = "approved"
                    manager_comments = "Approved for project completion"
                else:
                    status = "rejected"
                    manager_comments = "Not enough justification for overtime"
                
                overtime_request = models.OvertimeRequest(
                    user_id=user.id,
                    date=request_date.date(),
                    hours=hours,
                    reason=random.choice(reasons),
                    status=status,
                    manager_comments=manager_comments
                )
                
                db.add(overtime_request)
        
        # Commit all changes
        db.commit()
        
        print("Successfully initialized overtime request data")
        print("\nCreated sample overtime requests:")
        print("- 2-4 requests per user")
        print("- Random dates within last 3 months")
        print("- Random hours (1-8)")
        print("- Mix of pending, approved, and rejected statuses")
        
    except Exception as e:
        print(f"Error initializing overtime request data: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_overtime_requests() 