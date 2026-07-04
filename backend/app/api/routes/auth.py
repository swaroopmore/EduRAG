from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
def register(
    user: UserCreate,
    db: Session = Depends(get_db)
):

    service = AuthService(
        UserRepository(db)
    )

    try:

        created = service.register(
            user.full_name,
            user.email,
            user.password,
        )

        return {
            "message": "User registered successfully",
            "id": str(created.id),
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):

    service = AuthService(
        UserRepository(db)
    )

    try:

        token = service.login(
            request.email,
            request.password,
        )

        return {
            "access_token": token,
            "token_type": "bearer",
        }

    except ValueError as e:

        raise HTTPException(
            status_code=401,
            detail=str(e),
        )

@router.get("/me", response_model=UserResponse)
def me(
    current_user: User = Depends(get_current_user),
):
    return current_user