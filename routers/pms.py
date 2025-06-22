from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from sqlalchemy import extract
from database import get_db
import models
import schemas
from auth import get_current_user
from utils import verify_manager_permission, is_manager

router = APIRouter(
    prefix="/pms",
    tags=["Performance Management"]
)

# Goal Management Endpoints
@router.post("/goals", response_model=schemas.PerformanceGoal)
async def create_goal(
    goal: schemas.PerformanceGoalCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Create a new performance goal.
    - For self goals: goal_for should be "self" and user_id is not needed
    - For subordinate goals: goal_for should be "subordinate" and user_id is required
    """
    if goal.goal_for == "subordinate":
        if not goal.user_id:
            raise HTTPException(
                status_code=400,
                detail="user_id is required for subordinate goals"
            )
        # Verify manager permissions
        verify_manager_permission(db, current_user, goal.user_id)
        user_id = goal.user_id
    else:
        user_id = current_user.id

    db_goal = models.PerformanceGoal(
        user_id=user_id,
        title=goal.title,
        description=goal.description,
        target_date=goal.target_date,
        year=goal.year,
        goal_for=goal.goal_for,
        progress=goal.progress
    )
    
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    
    return db_goal

@router.get("/goals", response_model=List[schemas.GoalResponse])
async def get_my_goals(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get goals for the current user for a specific year.
    If year is not specified, returns goals for the current year.
    """
    if year is None:
        year = datetime.now().year
    goals = db.query(models.PerformanceGoal).filter(
        models.PerformanceGoal.user_id == current_user.id,
        models.PerformanceGoal.year == year
    ).all()
    return goals

@router.get("/goals/all", response_model=List[schemas.UserGoalsResponse])
async def get_all_goals(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get all goals for team members (manager only), grouped by user.
    If year is not specified, returns goals for the current year.
    """
    if not is_manager(db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can perform this action"
        )
        
    if year is None:
        year = datetime.now().year
    # Get all users who report to this manager
    team_members = db.query(models.User).filter(
        models.User.manager_id == current_user.id
    ).all()
    
    if not team_members:
        return []
    
    # Get goals for each team member
    result = []
    for member in team_members:
        goals = db.query(models.PerformanceGoal).filter(
            models.PerformanceGoal.user_id == member.id,
            models.PerformanceGoal.year == year
        ).order_by(
            models.PerformanceGoal.goal_id.asc()
        ).all()
        
        if goals:  # Only include users who have goals
            result.append({
                "user_id": member.id,
                "username": member.username,
                "full_name": member.full_name,
                "goals": goals
            })
    
    return result

@router.put("/goals/{goal_id}", response_model=schemas.PerformanceGoal)
async def update_goal(
    goal_id: int,
    goal_update: schemas.PerformanceGoalUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Update a performance goal.
    Only the goal owner can update their goals.
    """
    db_goal = db.query(models.PerformanceGoal).filter(
        models.PerformanceGoal.goal_id == goal_id,
        models.PerformanceGoal.user_id == current_user.id
    ).first()
    
    if not db_goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Update only the fields that are provided
    if goal_update.title is not None:
        db_goal.title = goal_update.title
    if goal_update.description is not None:
        db_goal.description = goal_update.description
    if goal_update.target_date is not None:
        db_goal.target_date = goal_update.target_date
    if goal_update.progress is not None:
        db_goal.progress = goal_update.progress
    
    db.commit()
    db.refresh(db_goal)
    
    return db_goal

@router.delete("/goals/{goal_id}")
async def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Delete a performance goal.
    """
    db_goal = db.query(models.PerformanceGoal).filter(
        models.PerformanceGoal.goal_id == goal_id
    ).first()
    
    if not db_goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Check if user has permission to delete
    if db_goal.user_id != current_user.id:
        # If not the owner, verify manager permissions
        verify_manager_permission(db, current_user, db_goal.user_id)
    
    db.delete(db_goal)
    db.commit()
    
    return {"message": "Goal deleted successfully"}

# Performance Review Endpoints
@router.post("/reviews", response_model=schemas.ReviewResponse)
async def create_self_review(
    review: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Create a self-review for a performance goal.
    """
    # Verify if the goal exists and belongs to the user
    db_goal = db.query(models.PerformanceGoal).filter(
        models.PerformanceGoal.goal_id == review.goal_id,
        models.PerformanceGoal.user_id == current_user.id
    ).first()
    
    if not db_goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Create the review
    db_review = models.PerformanceReview(
        user_id=current_user.id,
        goal_id=review.goal_id,
        year=db_goal.year,  # Get year from the goal
        achievements=review.achievements,
        rating_quality=review.rating_quality,
        rating_productivity=review.rating_productivity,
        rating_communication=review.rating_communication,
        overall_rating=review.overall_rating,
        status="pending"
    )
    
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    
    return db_review

@router.get("/reviews/report", response_model=List[schemas.GoalReviewReportItem])
async def get_performance_review_report(
    user_id: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get performance review report.
    - If user_id is provided, fetches report for that subordinate.
    - If user_id is not provided, fetches report for the current user.
    - If year is not specified, returns report for the current year.
    """
    target_user_id = current_user.id
    if user_id:
        # If a user_id is provided, verify manager permission
        verify_manager_permission(db, current_user, user_id)
        target_user_id = user_id

    if year is None:
        year = datetime.now().year
        
    # Fetch all goals for the target user for the specified year
    goals = db.query(models.PerformanceGoal).filter(
        models.PerformanceGoal.user_id == target_user_id,
        models.PerformanceGoal.year == year
    ).all()

    report = []
    for goal in goals:

        review = db.query(models.PerformanceReview).filter(
            models.PerformanceReview.goal_id == goal.goal_id
        ).first()
        report.append(schemas.GoalReviewReportItem(goal=goal, review=review))
    
    return report

@router.get("/reviews/all", response_model=List[schemas.ReviewResponse])
async def get_all_reviews(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get all reviews for team members (manager only).
    If year is not specified, returns reviews for the current year.
    """
    if not is_manager(db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can perform this action"
        )

    if year is None:
        year = datetime.now().year
    # Get all users who report to this manager
    team_members = db.query(models.User).filter(
        models.User.manager_id == current_user.id
    ).all()
    
    if not team_members:
        return []
    
    team_member_ids = [member.id for member in team_members]
    reviews = db.query(models.PerformanceReview).filter(
        models.PerformanceReview.user_id.in_(team_member_ids),
        models.PerformanceReview.year == year
    ).all()
    
    return reviews

@router.get("/reviews/pending", response_model=List[schemas.ReviewResponse])
async def get_pending_reviews_for_manager(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get all pending reviews for a manager's team members.
    If year is not specified, returns reviews for the current year.
    """
    if not is_manager(db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can perform this action"
        )
        
    if year is None:
        year = datetime.now().year
        
    # Get all users who report to this manager
    team_members = db.query(models.User).filter(
        models.User.manager_id == current_user.id
    ).all()
    
    if not team_members:
        return []
    
    team_member_ids = [member.id for member in team_members]
    
    reviews = db.query(models.PerformanceReview).filter(
        models.PerformanceReview.user_id.in_(team_member_ids),
        models.PerformanceReview.status == "pending",
        models.PerformanceReview.year == year
    ).all()
    
    return reviews

@router.put("/reviews/{review_id}/approve", response_model=schemas.ReviewResponse)
def approve_review(
    review_id: int,
    approval: schemas.ManagerReview,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve a performance review with manager's rating and comments.
    Only managers can approve reviews for their subordinates.
    """
    # Get the review
    review = db.query(models.PerformanceReview).filter(models.PerformanceReview.review_id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Check if review is already approved or rejected
    if review.status != "pending":
        raise HTTPException(
            status_code=400, 
            detail=f"Review is already {review.status}. Cannot approve a review that is not pending."
        )
    
    # Get the goal to check the user
    goal = db.query(models.PerformanceGoal).filter(models.PerformanceGoal.goal_id == review.goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Verify manager permissions
    verify_manager_permission(db, current_user, goal.user_id)
    
    # Update the review
    review.status = "approved"
    review.approver_rating_overall = approval.approver_rating_overall
    review.approver_comments = approval.approver_comments
    review.areas_for_improvement = approval.areas_for_improvement

    db.commit()
    db.refresh(review)
    return review

@router.put("/reviews/{review_id}/reject", response_model=schemas.ReviewResponse)
def reject_review(
    review_id: int,
    rejection: schemas.ReviewRejection,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject a performance review with rejection reason.
    Only managers can reject reviews for their subordinates.
    """
    # Get the review
    review = db.query(models.PerformanceReview).filter(models.PerformanceReview.review_id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Check if review is already approved or rejected
    if review.status != "pending":
        raise HTTPException(
            status_code=400, 
            detail=f"Review is already {review.status}. Cannot reject a review that is not pending."
        )
    
    # Get the goal to check the user
    goal = db.query(models.PerformanceGoal).filter(models.PerformanceGoal.goal_id == review.goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Verify manager permissions
    verify_manager_permission(db, current_user, goal.user_id)
    
    # Update the review
    review.status = "rejected"
    review.approver_comments = rejection.approver_comments
    
    db.commit()
    db.refresh(review)
    return review 