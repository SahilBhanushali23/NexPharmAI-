from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleResponse(RoleBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "OPERATOR"
    is_active: bool = True

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str = "OPERATOR"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
