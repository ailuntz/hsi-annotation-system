import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    full_name: str | None = Field(default=None, max_length=100)
    avatar: str | None = None


def validate_password_strength(password: str) -> str:
    """验证密码强度"""
    if len(password) < 8:
        raise ValueError("密码长度至少为 8 个字符")
    if len(password) > 128:
        raise ValueError("密码长度不能超过 128 个字符")
    if not re.search(r"[A-Za-z]", password):
        raise ValueError("密码必须包含至少一个字母")
    if not re.search(r"\d", password):
        raise ValueError("密码必须包含至少一个数字")
    return password


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return validate_password_strength(v)


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=100)
    avatar: str | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return validate_password_strength(v)


class UserResponse(UserBase):
    """Schema for user response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserInDB(UserBase):
    """Schema for user in database."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    hashed_password: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
