from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.auth import _check_password


class UserCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str

    _validate_password = field_validator("password")(_check_password)

    @field_validator("full_name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Name cannot be empty.")
        return value


class UserUpdate(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)

    @field_validator("full_name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Name cannot be empty.")
        return value


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime
