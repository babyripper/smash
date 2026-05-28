"""Weight Tracking Routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List

from app.database import get_db
from app.auth.jwt_handler import get_current_user
from app.models.user import User, UserRole
from app.models.weight import WeightTracking
from app.schemas.weight import WeightCreate, WeightResponse
from app.models.relationship import UserRelationship, RelationshipType

router = APIRouter()


@router.post("", response_model=WeightResponse, status_code=status.HTTP_201_CREATED)
async def create_weight_entry(
    weight_data: WeightCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new weight entry"""
    
    # Create weight tracking record
    weight_entry = WeightTracking(
        user_id=current_user.id,
        weight_date=weight_data.weight_date,
        weight_kg=weight_data.weight_kg,
        notes=weight_data.notes
    )
    
    db.add(weight_entry)
    db.commit()
    db.refresh(weight_entry)
    
    return weight_entry


@router.get("/{user_id}", response_model=List[WeightResponse])
async def get_user_weight_history(
    user_id: int,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get weight history for a specific user"""
    
    # Check permissions
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        # Check if current user is nutritionist or trainer for this user
        relationship = db.query(UserRelationship).filter(
            UserRelationship.professional_id == current_user.id,
            UserRelationship.user_id == user_id,
            UserRelationship.is_active == True
        ).first()
        
        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this user's weight data"
            )
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Query weight entries
    weights = db.query(WeightTracking).filter(
        WeightTracking.user_id == user_id,
        WeightTracking.weight_date >= start_date,
        WeightTracking.weight_date <= end_date
    ).order_by(WeightTracking.weight_date.asc()).all()
    
    return weights


@router.get("/my-weight", response_model=List[WeightResponse])
async def get_my_weight(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's weight history"""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    weights = db.query(WeightTracking).filter(
        WeightTracking.user_id == current_user.id,
        WeightTracking.weight_date >= start_date,
        WeightTracking.weight_date <= end_date
    ).order_by(WeightTracking.weight_date.asc()).all()
    
    return weights


@router.get("/my-weight/latest", response_model=WeightResponse)
async def get_latest_weight(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the latest weight entry"""
    
    latest = db.query(WeightTracking).filter(
        WeightTracking.user_id == current_user.id
    ).order_by(WeightTracking.weight_date.desc()).first()
    
    if not latest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No weight entries found"
        )
    
    return latest


@router.get("/my-weight/stats", response_model=dict)
async def get_weight_stats(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get weight statistics"""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    weights = db.query(WeightTracking).filter(
        WeightTracking.user_id == current_user.id,
        WeightTracking.weight_date >= start_date,
        WeightTracking.weight_date <= end_date
    ).order_by(WeightTracking.weight_date.asc()).all()
    
    if not weights:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No weight entries found"
        )
    
    weight_values = [w.weight_kg for w in weights]
    
    return {
        "current_weight": weight_values[-1],
        "min_weight": min(weight_values),
        "max_weight": max(weight_values),
        "average_weight": sum(weight_values) / len(weight_values),
        "weight_change": weight_values[-1] - weight_values[0],
        "total_entries": len(weight_values),
        "period_days": days
    }


@router.put("/{weight_id}", response_model=WeightResponse)
async def update_weight_entry(
    weight_id: int,
    weight_data: WeightCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a weight entry"""
    
    weight_entry = db.query(WeightTracking).filter(WeightTracking.id == weight_id).first()
    
    if not weight_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weight entry not found"
        )
    
    # Check permissions
    if weight_entry.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this weight entry"
        )
    
    weight_entry.weight_date = weight_data.weight_date
    weight_entry.weight_kg = weight_data.weight_kg
    weight_entry.notes = weight_data.notes
    
    db.commit()
    db.refresh(weight_entry)
    
    return weight_entry


@router.delete("/{weight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_weight_entry(
    weight_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a weight entry"""
    
    weight_entry = db.query(WeightTracking).filter(WeightTracking.id == weight_id).first()
    
    if not weight_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weight entry not found"
        )
    
    # Check permissions
    if weight_entry.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this weight entry"
        )
    
    db.delete(weight_entry)
    db.commit()
    
    return None
