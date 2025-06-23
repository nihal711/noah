from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from schemas import Token, LoginRequest, MessageResponse
from auth import authenticate_user, create_access_token, get_current_active_user
from config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post(
    "/login",
    response_model=Token,
    summary="Login User (use your email as username)",
    # description="Authenticate user and return access token.\n\n**IMPORTANT:** Enter your email address (e.g., john.doe@noah.com) in the 'username' field. The backend will authenticate using your actual email address, not your username.\n\n- username: (enter your email address)\n- password: (enter your password)\n\nThis applies to both the /auth/login endpoint and the Swagger 'Authorize' button."
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"name": user.username, "email": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout", response_model=MessageResponse, summary="Logout User", description="Logout current user (client-side token removal)")
async def logout(current_user = Depends(get_current_active_user)):
    """
    Logout endpoint. In a stateless JWT implementation, logout is typically handled 
    on the client side by removing the token. This endpoint confirms the user is authenticated.
    """
    return {"message": f"User {current_user.username} logged out successfully"}

@router.get("/me", summary="Get Current User", description="Get current authenticated user information")
async def read_users_me(current_user = Depends(get_current_active_user)):
    return current_user 