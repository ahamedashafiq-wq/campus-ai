from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole


class RegisterStudentIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=200)
    department: Optional[str] = Field(default=None, max_length=120)
    degree: Optional[str] = Field(default=None, max_length=120)
    graduation_year: Optional[int] = Field(default=None, ge=1990, le=2100)


class RegisterRecruiterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=200)
    company_name: str = Field(min_length=2, max_length=200)
    company_website: Optional[str] = Field(default=None, max_length=300)
    title: Optional[str] = Field(default=None, max_length=120)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    email_verified: bool


class PasswordResetRequestIn(BaseModel):
    email: EmailStr


class PasswordResetConfirmIn(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)
