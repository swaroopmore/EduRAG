from pydantic import BaseModel, EmailStr, Field, field_validator


def _check_password(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password is too long (maximum 72 bytes).")
    return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str

    _validate_new = field_validator("new_password")(_check_password)
