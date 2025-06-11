from sqlalchemy.orm import Session
from database import SessionLocal
from models import Course, Enrollment, Completion, User
from datetime import datetime, timedelta
import random

def init_lms_data():
    db = SessionLocal()
    try:
        # Create sample courses
        courses = [
            Course(
                title="Python Programming Fundamentals",
                description="Learn the basics of Python programming language",
                category="tech",
                instructor="John Smith",
                duration=40,
                is_active=True
            ),
            Course(
                title="Web Development with React",
                description="Master modern web development using React",
                category="tech",
                instructor="Sarah Johnson",
                duration=60,
                is_active=True
            ),
            Course(
                title="Data Science Essentials",
                description="Introduction to data science and analytics",
                category="data",
                instructor="Michael Brown",
                duration=50,
                is_active=True
            ),
            Course(
                title="Project Management",
                description="Learn effective project management techniques",
                category="business",
                instructor="Emily Davis",
                duration=30,
                is_active=True
            ),
            Course(
                title="Digital Marketing",
                description="Comprehensive guide to digital marketing strategies",
                category="marketing",
                instructor="David Wilson",
                duration=45,
                is_active=True
            )
        ]
        
        # Add courses to database
        for course in courses:
            db.add(course)
        db.commit()
        
        # Get all courses and users
        courses = db.query(Course).all()
        users = db.query(User).all()
        
        # Create sample enrollments
        enrollment_statuses = ['active', 'completed', 'dropped']
        for user in users:
            # Each user enrolls in 2-3 random courses
            num_enrollments = random.randint(2, 3)
            selected_courses = random.sample(courses, num_enrollments)
            
            for course in selected_courses:
                # Random enrollment date within last 6 months
                enrollment_date = datetime.utcnow() - timedelta(days=random.randint(0, 180))
                
                enrollment = Enrollment(
                    user_id=user.id,
                    course_id=course.course_id,
                    enrolled_at=enrollment_date,
                    status=random.choice(enrollment_statuses),
                    progress=random.randint(0, 100)
                )
                db.add(enrollment)
        
        db.commit()
        
        # Create sample completions
        for user in users:
            # Get user's completed enrollments
            completed_enrollments = db.query(Enrollment).filter(
                Enrollment.user_id == user.id,
                Enrollment.status == 'completed'
            ).all()
            
            for enrollment in completed_enrollments:
                # Check if completion record already exists
                existing_completion = db.query(Completion).filter(
                    Completion.user_id == user.id,
                    Completion.course_id == enrollment.course_id
                ).first()
                
                if not existing_completion:
                    completion = Completion(
                        user_id=user.id,
                        course_id=enrollment.course_id,
                        completed_at=enrollment.enrolled_at + timedelta(days=random.randint(30, 90)),
                        certificate_url=f"https://example.com/certificates/{user.id}_{enrollment.course_id}.pdf"
                    )
                    db.add(completion)
        
        db.commit()
        print("Successfully initialized LMS data")
        
    except Exception as e:
        print(f"Error initializing LMS data: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_lms_data() 