from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.core.rate_limit import client_ip, limiter
from app.database.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import ChangePasswordRequest, LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=201)
def register(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    limiter.check(
        f"register:{client_ip(request)}",
        settings.REGISTER_RATE_LIMIT_PER_HOUR,
        3600,
    )
    created = AuthService(UserRepository(db)).register(
        user.full_name, user.email, user.password
    )
    return {"message": "User registered successfully", "id": str(created.id)}


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    limiter.check(
        f"login:{client_ip(request)}:{payload.email.lower()}",
        settings.LOGIN_RATE_LIMIT_PER_5_MIN,
        300,
    )
    token = AuthService(UserRepository(db)).login(payload.email, payload.password)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AuthService(UserRepository(db)).update_profile(current_user, payload.full_name)


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    AuthService(UserRepository(db)).change_password(
        current_user, payload.current_password, payload.new_password
    )
    return {"message": "Password updated successfully"}
