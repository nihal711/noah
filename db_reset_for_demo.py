from sqlalchemy.orm import Session
from database import engine
import models


def db_reset_for_demo():
    session = Session(bind=engine)
    try:
        # Delete OvertimeLeave (depends on OvertimeRequest)
        session.query(models.OvertimeLeave).delete()

        # Delete OvertimeRequest
        session.query(models.OvertimeRequest).delete()

        # Delete Attachments for BankLetterRequest and VisaLetterRequest
        session.query(models.Attachment).filter(
            (models.Attachment.bank_letter_request_id != None) |
            (models.Attachment.visa_letter_request_id != None)
        ).delete(synchronize_session=False)

        # Delete BankLetterRequest
        session.query(models.BankLetterRequest).delete()

        # Delete VisaLetterRequest
        session.query(models.VisaLetterRequest).delete()

        # Delete LeaveRequest
        session.query(models.LeaveRequest).delete()

        # Reset LeaveBalance: used_days=0, remaining_days=total_days
        leave_balances = session.query(models.LeaveBalance).all()
        for lb in leave_balances:
            lb.used_days = 0
            lb.remaining_days = lb.total_days
        session.commit()
        print("data reset successfully.")
    except Exception as e:
        session.rollback()
        print("Error during reset:", e)
    finally:
        session.close()


if __name__ == "__main__":
    db_reset_for_demo() 