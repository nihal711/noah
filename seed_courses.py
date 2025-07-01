from datetime import date, timedelta
from database import SessionLocal
from models import Course, CourseCategory

def reset_lms_data():
    session = SessionLocal()
    try:
        # Delete all courses
        session.query(Course).delete()
        session.commit()

        today = date.today()

        # Ongoing courses (today is between start and end)
        ongoing_courses = [
            Course(
                title="Python for Beginners",
                description="Intro to Python programming.",
                category=CourseCategory.TECH,
                instructor="Jane Doe",
                start_date=today - timedelta(days=5),
                end_date=today + timedelta(days=10),
                duration=15,
                is_active=True
            ),
            Course(
                title="HR Compliance Essentials",
                description="Key HR policies and compliance.",
                category=CourseCategory.HR,
                instructor="John Smith",
                start_date=today - timedelta(days=3),
                end_date=today + timedelta(days=7),
                duration=10,
                is_active=True
            ),
        ]

        # Upcoming courses (start date in the future)
        upcoming_courses = [
            # TECH
            Course(
                title="Advanced Python",
                description="Deep dive into Python topics.",
                category=CourseCategory.TECH,
                instructor="Sara White",
                start_date=today + timedelta(days=7),
                end_date=today + timedelta(days=27),
                duration=20,
                is_active=True
            ),
            Course(
                title="DevOps Fundamentals",
                description="Learn DevOps culture and tools.",
                category=CourseCategory.TECH,
                instructor="Michael Green",
                start_date=today + timedelta(days=15),
                end_date=today + timedelta(days=35),
                duration=20,
                is_active=True
            ),
            # HR
            Course(
                title="Workplace Diversity & Inclusion",
                description="Best practices for diverse teams.",
                category=CourseCategory.HR,
                instructor="Linda Brown",
                start_date=today + timedelta(days=8),
                end_date=today + timedelta(days=18),
                duration=10,
                is_active=True
            ),
            Course(
                title="Conflict Resolution in HR",
                description="Managing disputes effectively.",
                category=CourseCategory.HR,
                instructor="Mark Davis",
                start_date=today + timedelta(days=12),
                end_date=today + timedelta(days=22),
                duration=10,
                is_active=True
            ),
            # MARKETING
            Course(
                title="Digital Marketing Mastery",
                description="Modern digital marketing strategies.",
                category=CourseCategory.MARKETING,
                instructor="Alice Johnson",
                start_date=today + timedelta(days=5),
                end_date=today + timedelta(days=25),
                duration=20,
                is_active=True
            ),
            Course(
                title="Brand Building Essentials",
                description="How to build a strong brand identity.",
                category=CourseCategory.MARKETING,
                instructor="Nina Patel",
                start_date=today + timedelta(days=14),
                end_date=today + timedelta(days=29),
                duration=15,
                is_active=True
            ),
            # FINANCE
            Course(
                title="Finance for Non-Finance Managers",
                description="Finance basics for all managers.",
                category=CourseCategory.FINANCE,
                instructor="Bob Lee",
                start_date=today + timedelta(days=10),
                end_date=today + timedelta(days=30),
                duration=20,
                is_active=True
            ),
            Course(
                title="Budgeting and Forecasting",
                description="Effective financial planning skills.",
                category=CourseCategory.FINANCE,
                instructor="Emily Carter",
                start_date=today + timedelta(days=18),
                end_date=today + timedelta(days=38),
                duration=20,
                is_active=True
            ),
        ]

        courses = ongoing_courses + upcoming_courses
        session.add_all(courses)
        session.commit()
    finally:
        session.close()

if __name__ == "__main__":
    reset_lms_data()
    print("LMS data reset: ongoing and upcoming courses added (2 per category for upcoming).")
