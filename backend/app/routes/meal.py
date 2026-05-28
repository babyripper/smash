"""Meal Diary Routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List

from app.database import get_db
from app.auth.jwt_handler import get_current_user
from app.models.user import User, UserRole
from app.models.meal_diary import MealDiary
from app.schemas.meal import MealDiaryCreate, MealDiaryResponse
from app.models.relationship import UserRelationship, RelationshipType

router = APIRouter()


@router.post("", response_model=MealDiaryResponse, status_code=status.HTTP_201_CREATED)
async def create_meal_entry(
    meal_data: MealDiaryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new meal diary entry"""
    
    meal_entry = MealDiary(
        user_id=current_user.id,
        meal_date=meal_data.meal_date,
        meal_type=meal_data.meal_type,
        description=meal_data.description,
        quantity=meal_data.quantity,
        hydration_ml=meal_data.hydration_ml,
        respected_diet=meal_data.respected_diet,
        mood=meal_data.mood,
        notes=meal_data.notes
    )
    
    db.add(meal_entry)
    db.commit()
    db.refresh(meal_entry)
    
    return meal_entry


@router.get("/{user_id}", response_model=List[MealDiaryResponse])
async def get_user_meals(
    user_id: int,
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get meal diary entries for a specific user"""
    
    # Check permissions
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        # Check if current user is nutritionist for this user
        relationship = db.query(UserRelationship).filter(
            UserRelationship.professional_id == current_user.id,
            UserRelationship.user_id == user_id,
            UserRelationship.relationship_type == RelationshipType.NUTRITIONIST,
            UserRelationship.is_active == True
        ).first()
        
        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these meal entries"
            )
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    meals = db.query(MealDiary).filter(
        MealDiary.user_id == user_id,
        MealDiary.meal_date >= start_date,
        MealDiary.meal_date <= end_date
    ).order_by(MealDiary.meal_date.desc()).all()
    
    return meals


@router.get("/my-meals", response_model=List[MealDiaryResponse])
async def get_my_meals(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's meal diary entries"""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    meals = db.query(MealDiary).filter(
        MealDiary.user_id == current_user.id,
        MealDiary.meal_date >= start_date,
        MealDiary.meal_date <= end_date
    ).order_by(MealDiary.meal_date.desc()).all()
    
    return meals


@router.get("/my-meals/today", response_model=List[MealDiaryResponse])
async def get_today_meals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get today's meal entries"""
    
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    meals = db.query(MealDiary).filter(
        MealDiary.user_id == current_user.id,
        MealDiary.meal_date >= today_start,
        MealDiary.meal_date < today_end
    ).order_by(MealDiary.meal_date.asc()).all()
    
    return meals


@router.get("/my-meals/diet-respect", response_model=dict)
async def get_diet_compliance(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get diet compliance statistics"""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    meals = db.query(MealDiary).filter(
        MealDiary.user_id == current_user.id,
        MealDiary.meal_date >= start_date,
        MealDiary.meal_date <= end_date
    ).all()
    
    if not meals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No meal entries found"
        )
    
    total_meals = len(meals)
    respected = sum(1 for m in meals if m.respected_diet)
    not_respected = total_meals - respected
    compliance_percentage = (respected / total_meals * 100) if total_meals > 0 else 0
    
    # Calculate average hydration
    hydrations = [m.hydration_ml for m in meals if m.hydration_ml is not None]
    avg_hydration = sum(hydrations) / len(hydrations) if hydrations else 0
    
    return {
        "total_meals": total_meals,
        "respected_diet": respected,
        "not_respected_diet": not_respected,
        "compliance_percentage": round(compliance_percentage, 2),
        "average_hydration_ml": round(avg_hydration, 2),
        "period_days": days
    }


@router.put("/{meal_id}", response_model=MealDiaryResponse)
async def update_meal_entry(
    meal_id: int,
    meal_data: MealDiaryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a meal diary entry"""
    
    meal = db.query(MealDiary).filter(MealDiary.id == meal_id).first()
    
    if not meal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal entry not found"
        )
    
    # Check permissions
    if meal.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this meal entry"
        )
    
    meal.meal_date = meal_data.meal_date
    meal.meal_type = meal_data.meal_type
    meal.description = meal_data.description
    meal.quantity = meal_data.quantity
    meal.hydration_ml = meal_data.hydration_ml
    meal.respected_diet = meal_data.respected_diet
    meal.mood = meal_data.mood
    meal.notes = meal_data.notes
    
    db.commit()
    db.refresh(meal)
    
    return meal


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_entry(
    meal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a meal diary entry"""
    
    meal = db.query(MealDiary).filter(MealDiary.id == meal_id).first()
    
    if not meal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal entry not found"
        )
    
    # Check permissions
    if meal.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this meal entry"
        )
    
    db.delete(meal)
    db.commit()
    
    return None
