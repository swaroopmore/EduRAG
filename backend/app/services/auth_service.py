from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
)


class AuthService:

    def __init__(self, repository: UserRepository):
        self.repository = repository

    def register(
        self,
        full_name: str,
        email: str,
        password: str,
    ):
        existing = self.repository.get_by_email(email)

        if existing:
            raise ValueError("Email already registered")

        user = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
        )

        return self.repository.create(user)

    def login(
        self,
        email: str,
        password: str,
    ):
        user = self.repository.get_by_email(email)

        if not user:
            raise ValueError("Invalid credentials")

        if not verify_password(
            password,
            user.password_hash,
        ):
            raise ValueError("Invalid credentials")

        token = create_access_token(
            {
                "sub": str(user.id)
            }
        )

        return token