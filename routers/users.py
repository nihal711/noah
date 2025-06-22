from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import UserCreate, UserResponse, MessageResponse
from auth import get_password_hash, get_current_active_user, get_current_user

router = APIRouter(prefix="/users", tags=["User Management"])

@router.post("/", response_model=UserResponse, summary="Create User", description="Create a new user account")
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username already exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if employee_id already exists
    db_user = db.query(User).filter(User.employee_id == user.employee_id).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Employee ID already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        employee_id=user.employee_id,
        department=user.department,
        position=user.position,
        manager_id=user.manager_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/", response_model=List[UserResponse], summary="Get All Users", description="Retrieve all users (admin function)")
async def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=UserResponse, summary="Get User by ID", description="Retrieve a specific user by ID")
async def read_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/subordinates/", response_model=List[UserResponse], summary="Get a list of direct subordinates")
async def get_subordinates(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Returns a list of users who report directly to the current user.
    """
    subordinates = db.query(User).filter(User.manager_id == current_user.id).all()
    
    if not subordinates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't have any subordinates"
        )
        
    return subordinates

@router.delete("/{user_id}", response_model=MessageResponse, summary="Delete User", description="Delete a user account")
async def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"message": f"User {user.username} deleted successfully"} 