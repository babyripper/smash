"""Workout Management Routes"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
import os
from pathlib import Path

from app.database import get_db
from app.auth.jwt_handler import get_current_user
from app.models.user import User, UserRole
from app.models.workout import Workout, WorkoutPlan
from app.schemas.workout import WorkoutCreate, WorkoutResponse, WorkoutPlanCreate
from app.models.relationship import UserRelationship, RelationshipType

router = APIRouter()

# Directory for storing uploaded files
UPLOAD_DIR = Path("uploads/workout_plans")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/plans/upload", status_code=status.HTTP_201_CREATED)
async def upload_workout_plan(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a workout plan PDF"""
    
    # Check permissions
    if current_user.role == UserRole.PERSONAL_TRAINER:
        # Trainer può caricare
        pass
    elif current_user.role == UserRole.ADMIN or current_user.role == UserRole.USER:
        # Admin e User possono caricare per se stessi
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to upload workout plan"
        )
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Save file
    file_path = UPLOAD_DIR / f"{current_user.id}_{file.filename}"
    contents = await file.read()
    
    with open(file_path, 'wb') as f:
        f.write(contents)
    
    # Create workout plan record
    uploaded_by = "trainer" if current_user.role == UserRole.PERSONAL_TRAINER else "user"
    
    plan = WorkoutPlan(
        user_id=current_user.id,
        trainer_id=current_user.id if current_user.role == UserRole.PERSONAL_TRAINER else None,
        file_path=str(file_path),
        file_name=file.filename,
        file_size=len(contents),
        uploaded_by=uploaded_by
    )
    
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    return {
        "id": plan.id,
        "user_id": plan.user_id,
        "file_name": plan.file_name,
        "uploaded_by": plan.uploaded_by,
        "created_at": plan.created_at
    }


@router.get("/plans/{user_id}")
async def get_user_workout_plans(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get workout plans for a specific user"""
    
    # Check permissions
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        # Check if current user is trainer for this user
        relationship = db.query(UserRelationship).filter(
            UserRelationship.professional_id == current_user.id,
            UserRelationship.user_id == user_id,
            UserRelationship.relationship_type == RelationshipType.PERSONAL_TRAINER,
            UserRelationship.is_active == True
        ).first()
        
        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these workout plans"
            )
    
    plans = db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user_id).all()
    return plans


@router.get("/plans/my-plans")
async def get_my_workout_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's workout plans"""
    
    plans = db.query(WorkoutPlan).filter(WorkoutPlan.user_id == current_user.id).all()
    return plans


@router.post("", response_model=WorkoutResponse, status_code=status.HTTP_201_CREATED)
async def create_workout(
    workout_data: WorkoutCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new workout entry"""
    
    workout = Workout(
        user_id=current_user.id,
        workout_date=workout_data.workout_date,
        workout_type=workout_data.workout_type,
        muscle_groups=workout_data.muscle_groups,
        duration_minutes=workout_data.duration_minutes,
        intensity=workout_data.intensity,
        post_workout_mood=workout_data.post_workout_mood,
        exercises=workout_data.exercises,
        notes=workout_data.notes
    )
    
    db.add(workout)
    db.commit()
    db.refresh(workout)
    
    return workout


@router.get("/{user_id}", response_model=List[WorkoutResponse])
async def get_user_workouts(
    user_id: int,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get workouts for a specific user"""
    
    # Check permissions
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        # Check if current user is trainer for this user
        relationship = db.query(UserRelationship).filter(
            UserRelationship.professional_id == current_user.id,
            UserRelationship.user_id == user_id,
            UserRelationship.relationship_type == RelationshipType.PERSONAL_TRAINER,
            UserRelationship.is_active == True
        ).first()
        
        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these workouts"
            )
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    workouts = db.query(Workout).filter(
        Workout.user_id == user_id,
        Workout.workout_date >= start_date,
        Workout.workout_date <= end_date
    ).order_by(Workout.workout_date.desc()).all()
    
    return workouts


@router.get("/my-workouts", response_model=List[WorkoutResponse])
async def get_my_workouts(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's workouts"""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    workouts = db.query(Workout).filter(
        Workout.user_id == current_user.id,
        Workout.workout_date >= start_date,
        Workout.workout_date <= end_date
    ).order_by(Workout.workout_date.desc()).all()
    
    return workouts


@router.get("/my-workouts/stats", response_model=dict)
async def get_workout_stats(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get workout statistics"""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    workouts = db.query(Workout).filter(
        Workout.user_id == current_user.id,
        Workout.workout_date >= start_date,
        Workout.workout_date <= end_date
    ).all()
    
    if not workouts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No workouts found"
        )
    
    total_duration = sum(w.duration_minutes or 0 for w in workouts)
    avg_duration = total_duration / len(workouts) if workouts else 0
    
    return {
        "total_workouts": len(workouts),
        "total_duration_minutes": total_duration,
        "average_duration_minutes": round(avg_duration, 2),
        "period_days": days
    }


@router.put("/{workout_id}", response_model=WorkoutResponse)
async def update_workout(
    workout_id: int,
    workout_data: WorkoutCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a workout entry"""
    
    workout = db.query(Workout).filter(Workout.id == workout_id).first()
    
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found"
        )
    
    # Check permissions
    if workout.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this workout"
        )
    
    workout.workout_date = workout_data.workout_date
    workout.workout_type = workout_data.workout_type
    workout.muscle_groups = workout_data.muscle_groups
    workout.duration_minutes = workout_data.duration_minutes
    workout.intensity = workout_data.intensity
    workout.post_workout_mood = workout_data.post_workout_mood
    workout.exercises = workout_data.exercises
    workout.notes = workout_data.notes
    
    db.commit()
    db.refresh(workout)
    
    return workout


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workout(
    workout_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a workout entry"""
    
    workout = db.query(Workout).filter(Workout.id == workout_id).first()
    
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found"
        )
    
    # Check permissions
    if workout.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this workout"
        )
    
    db.delete(workout)
    db.commit()
    
    return None
