from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import date
from database import SessionLocal
from models import Course

def deactivate_past_courses():
    session = SessionLocal()
    try:
        today = date.today()
        courses = session.query(Course).filter(Course.end_date < today, Course.is_active == True).all()
        for course in courses:
            course.is_active = False
        session.commit()
        print(f"Deactivated {len(courses)} past courses.")
    finally:
        session.close()

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    # Run every day at midnight
    scheduler.add_job(deactivate_past_courses, 'cron', hour=0, minute=0)
    print("Scheduler started. Deactivation will run daily at midnight.")
    scheduler.start() 