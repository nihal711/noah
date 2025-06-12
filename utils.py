from sqlalchemy.orm import Session
from models import User
from fastapi import HTTPException, status

def is_manager(db: Session, user: User) -> bool:
    """
    Check if user is a manager (has subordinates)
    
    Args:
        db: Database session
        user: User to check
        
    Returns:
        bool: True if user is a manager, False otherwise
    """
    # Check if any user has this user as their manager
    subordinates = db.query(User).filter(User.manager_id == user.id).first()
    return subordinates is not None

def is_subordinate(db: Session, manager: User, user_id: int) -> bool:
    """
    Check if user_id is a subordinate of the manager
    
    Args:
        db: Database session
        manager: Manager user
        user_id: ID of the user to check
        
    Returns:
        bool: True if user is a subordinate of the manager, False otherwise
    """
    # Get the target user
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        return False
    # Check if target user's manager is the given manager
    return target_user.manager_id == manager.id

def verify_manager_permission(db: Session, current_user: User, target_user_id: int) -> None:
    """
    Verify that the current user is a manager and the target user is their subordinate.
    Raises appropriate HTTP exceptions if checks fail.
    
    Args:
        db: Database session
        current_user: Current user (manager)
        target_user_id: ID of the target user (subordinate)
        
    Raises:
        HTTPException: If current user is not a manager or target user is not their subordinate
    """
    if not is_manager(db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can perform this action"
        )
    
    if not is_subordinate(db, current_user, target_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only perform this action for your direct subordinates"
        ) 