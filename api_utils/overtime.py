from datetime import datetime
import calendar

def calculate_overtime_entitlement(user, date, hours, grade, year_total_hours):
    """
    Calculate entitled overtime hours and leave days based on business rules.
    Args:
        user: User object (must have grade attribute as int or str)
        date: datetime.date or str (YYYY-MM-DD)
        hours: float, number of OT hours for the request
        grade: int or str, user grade (1-5)
        year_total_hours: float, total OT hours already approved for this year
    Returns:
        dict: {
            'entitled_hours': float,
            'entitled_leave_days': float,
            'capped': bool,
            'message': str
        }
    """
    # Parse date if string
    if isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d").date()
    
    # Determine if weekend
    weekday = date.weekday()  # 0=Mon, 6=Sun
    is_weekend = weekday >= 5
    
    # Apply multiplier
    multiplier = 2.0 if is_weekend else 1.5
    grade = int(grade)
    
    # Grade rules
    if grade in [1, 2, 3]:
        entitled_hours = hours * multiplier
        grade_rule_msg = "All OT hours are counted."
    elif grade in [4, 5]:
        capped_hours = min(hours, 4)
        entitled_hours = capped_hours * multiplier
        if hours > 4:
            grade_rule_msg = f"Only first 4 hours counted for entitlement; extra {hours-4:.2f}h ignored."
        else:
            grade_rule_msg = "Max 4 OT hours per day counted."
    else:
        entitled_hours = 0
        grade_rule_msg = "Unknown grade. No entitlement."
    
    # Calculate total hours for year (including this request)
    total_hours = year_total_hours + entitled_hours
    leave_days = total_hours // 8  # Floor division
    leave_days_capped = min(leave_days, 9)
    capped = leave_days > 9
    
    # Message
    if capped:
        message = (
            f"This request would bring your total OT leave days to {leave_days:.0f}, "
            f"but the maximum allowed is 9 per year. Please contact HR for exceptions. "
            f"(HR: hr@example.com)"
        )
    else:
        message = (
            f"This request will grant you {entitled_hours:.2f} entitled OT hours, "
            f"which is {entitled_hours/8:.2f} leave days upon approval. "
            f"{grade_rule_msg}"
        )
    
    return {
        'entitled_hours': entitled_hours,
        'entitled_leave_days': entitled_hours / 8,
        'capped': capped,
        'message': message
    } 