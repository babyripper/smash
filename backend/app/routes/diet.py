"""Diet Management Routes"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import os
from pathlib import Path

from app.database import get_db
from app.auth.jwt_handler import get_current_user
from app.models.user import User, UserRole
from app.models.diet import Diet, UploadedBy
from app.schemas.diet import DietCreate, DietResponse
from app.permissions.decorators import check_permission

router = APIRouter()

# Directory for storing uploaded files
UPLOAD_DIR = Path("uploads/diets")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload", response_model=DietResponse, status_code=status.HTTP_201_CREATED)
async def upload_diet(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a diet PDF"""
    
    # Check permissions
    if current_user.role == UserRole.NUTRITIONIST:
        # Nutrizionista può caricare
        pass
    elif current_user.role == UserRole.ADMIN or current_user.role == UserRole.USER:
        # Admin e User possono caricare per se stessi
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to upload diet"
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
    
    # Determine who uploaded
    uploaded_by = UploadedBy.USER if current_user.role == UserRole.USER else UploadedBy.NUTRITIONIST
    
    # Create diet record
    diet = Diet(
        user_id=current_user.id,
        nutritionist_id=current_user.id if current_user.role == UserRole.NUTRITIONIST else None,
        file_path=str(file_path),
        file_name=file.filename,
        file_size=len(contents),
        uploaded_by=uploaded_by
    )
    
    db.add(diet)
    db.commit()
    db.refresh(diet)
    
    return diet


@router.get("/{user_id}", response_model=list[DietResponse])
async def get_user_diets(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get diets for a specific user"""
    
    # Check if user can access this data
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        # Check if current user is nutritionist for this user
        from app.models.relationship import UserRelationship, RelationshipType
        relationship = db.query(UserRelationship).filter(
            UserRelationship.professional_id == current_user.id,
            UserRelationship.user_id == user_id,
            UserRelationship.relationship_type == RelationshipType.NUTRITIONIST,
            UserRelationship.is_active == True
        ).first()
        
        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these diets"
            )
    
    diets = db.query(Diet).filter(Diet.user_id == user_id).all()
    return diets


@router.get("/my-diets", response_model=list[DietResponse])
async def get_my_diets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's diets"""
    
    diets = db.query(Diet).filter(Diet.user_id == current_user.id).all()
    return diets


@router.delete("/{diet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_diet(
    diet_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a diet"""
    
    diet = db.query(Diet).filter(Diet.id == diet_id).first()
    
    if not diet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diet not found"
        )
    
    # Check permissions
    if diet.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this diet"
        )
    
    # Delete file
    if os.path.exists(diet.file_path):
        os.remove(diet.file_path)
    
    db.delete(diet)
    db.commit()
    
    return None
