from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, Role
from app.schemas.user import UserCreate, UserLogin
from app.core.security import get_password_hash, verify_password, create_access_token
from app.utils.logger import logger

DEFAULT_ROLES = [
    ("ADMIN", "System administrator with full platform access"),
    ("PRODUCTION_MANAGER", "Production scheduling, batch oversight, inventory, analytics"),
    ("MAINTENANCE_MANAGER", "Machine reliability, health monitoring, work orders, alerts"),
    ("QUALITY_MANAGER", "Batch quality inspection, risk analytics, release approval"),
    ("OPERATOR", "Equipment operation, telemetry inspection, operational execution")
]

class AuthService:
    @staticmethod
    def initialize_default_roles(db: Session):
        for name, desc in DEFAULT_ROLES:
            existing = db.query(Role).filter(Role.name == name).first()
            if not existing:
                role = Role(name=name, description=desc)
                db.add(role)
        db.commit()

    @staticmethod
    def register_user(db: Session, user_in: UserCreate) -> User:
        # Check if email exists
        existing = db.query(User).filter(User.email == user_in.email.lower()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists."
            )

        # Validate role
        valid_roles = [r[0] for r in DEFAULT_ROLES]
        role_name = user_in.role.upper()
        if role_name not in valid_roles:
            role_name = "OPERATOR"

        # Create user
        user = User(
            email=user_in.email.lower(),
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            role=role_name,
            is_active=True
        )

        # Attach role object if exists
        role_obj = db.query(Role).filter(Role.name == role_name).first()
        if role_obj:
            user.roles.append(role_obj)

        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Registered new user {user.email} with role {user.role}")
        return user

    @staticmethod
    def authenticate_user(db: Session, credentials: UserLogin) -> dict:
        user = db.query(User).filter(User.email == credentials.email.lower()).first()
        if not user or not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        access_token = create_access_token(subject=user.id)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
