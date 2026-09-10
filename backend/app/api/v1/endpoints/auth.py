from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.services.auth import AuthService

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Register a new user")
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new platform user with specified role (ADMIN, PRODUCTION_MANAGER, MAINTENANCE_MANAGER, QUALITY_MANAGER, OPERATOR).
    """
    return AuthService.register_user(db, user_in)

@router.post("/login", response_model=TokenResponse, summary="User authentication and JWT token generation")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user via JSON credentials and issue signed JWT bearer token.
    """
    return AuthService.authenticate_user(db, credentials)

@router.post("/login/access-token", response_model=TokenResponse, summary="OAuth2 form compatible login")
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2 Password Request Form standard login for Swagger UI integration.
    """
    credentials = UserLogin(email=form_data.username, password=form_data.password)
    return AuthService.authenticate_user(db, credentials)

@router.get("/me", response_model=UserResponse, summary="Get current logged in user profile")
def read_current_user(current_user: User = Depends(get_current_user)):
    """
    Retrieve profile and permissions for currently authenticated token holder.
    """
    return current_user
