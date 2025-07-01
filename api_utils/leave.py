from models import User

def is_leave_type_eligible(user: User, leave_type: str) -> bool:
    leave_type = leave_type.lower()
    gender = user.gender.strip().lower() if user.gender else ""
    religion = user.religion.strip().lower() if hasattr(user, 'religion') and user.religion else ""
    if leave_type == "maternity":
        return gender == "female"
    if leave_type == "paternity":
        return gender == "male"
    if leave_type == "hajj":
        return religion == "muslim"
    # All other leave types are allowed for everyone
    return True 