from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, RoleChecker
from app.models.user import User, Role
from app.schemas.user import UserResponse, UserUpdate, RoleResponse

router = APIRouter()

# Admin only access
admin_required = RoleChecker(["ADMIN"])

@router.get("", response_model=List[UserResponse], summary="List all platform users (Admin)")
def list_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(admin_required)
):
    return db.query(User).offset(skip).limit(limit).all()

@router.get("/roles", response_model=List[RoleResponse], summary="List available roles")
def list_roles(db: Session = Depends(get_db)):
    return db.query(Role).all()

@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID (Admin)")
def get_user_by_id(
    user_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(admin_required)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/{user_id}", response_model=UserResponse, summary="Update user profile or role (Admin)")
def update_user(
    user_id: str,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(admin_required)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.role is not None:
        user.role = user_in.role.upper()
    if user_in.is_active is not None:
        user.is_active = user_in.is_active

    db.commit()
    db.refresh(user)
    return user
