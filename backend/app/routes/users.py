"""User Management Routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.jwt_handler import get_current_user
from app.models.user import User, UserRole
from app.models.relationship import UserRelationship, RelationshipType
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user's profile"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    first_name: str = None,
    last_name: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    
    if first_name:
        current_user.first_name = first_name
    if last_name:
        current_user.last_name = last_name
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.post("/invite-professional/{professional_id}")
async def invite_professional(
    professional_id: int,
    relationship_type: RelationshipType,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invite a nutritionist or personal trainer"""
    
    # Get professional
    professional = db.query(User).filter(User.id == professional_id).first()
    
    if not professional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional not found"
        )
    
    # Check if professional has correct role
    if relationship_type == RelationshipType.NUTRITIONIST:
        if professional.role != UserRole.NUTRITIONIST:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not a nutritionist"
            )
    elif relationship_type == RelationshipType.PERSONAL_TRAINER:
        if professional.role != UserRole.PERSONAL_TRAINER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not a personal trainer"
            )
    
    # Check if relationship already exists
    existing = db.query(UserRelationship).filter(
        UserRelationship.user_id == current_user.id,
        UserRelationship.professional_id == professional_id,
        UserRelationship.relationship_type == relationship_type
    ).first()
    
    if existing and existing.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Relationship already exists"
        )
    
    # Create or reactivate relationship
    if existing:
        existing.is_active = True
        existing.ended_at = None
        db.commit()
    else:
        relationship = UserRelationship(
            user_id=current_user.id,
            professional_id=professional_id,
            relationship_type=relationship_type,
            is_active=True
        )
        db.add(relationship)
        db.commit()
    
    return {
        "message": f"{relationship_type.value} invited successfully",
        "professional_id": professional_id
    }


@router.get("/professionals")
async def get_my_professionals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's connected professionals"""
    
    relationships = db.query(UserRelationship).filter(
        UserRelationship.user_id == current_user.id,
        UserRelationship.is_active == True
    ).all()
    
    professionals = []
    for rel in relationships:
        prof = db.query(User).filter(User.id == rel.professional_id).first()
        if prof:
            professionals.append({
                "id": prof.id,
                "email": prof.email,
                "name": f"{prof.first_name} {prof.last_name}".strip(),
                "role": prof.role,
                "relationship_type": rel.relationship_type,
                "connected_since": rel.started_at
            })
    
    return professionals


@router.delete("/professionals/{professional_id}")
async def remove_professional(
    professional_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a professional connection"""
    
    relationship = db.query(UserRelationship).filter(
        UserRelationship.user_id == current_user.id,
        UserRelationship.professional_id == professional_id
    ).first()
    
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship not found"
        )
    
    relationship.is_active = False
    db.commit()
    
    return {"message": "Professional connection removed"}
