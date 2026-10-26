from app.auth.security import (
    burn_password_check,
    create_access_token,
    hash_password,
    verify_password,
)
from app.core.errors import AppError, UnauthorizedError
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def register(self, full_name: str, email: str, password: str) -> User:
        email = email.strip().lower()
        if self.repository.get_by_email(email):
            raise AppError("An account with this email already exists.", code="email_taken")

        user = User(
            full_name=full_name.strip(),
            email=email,
            password_hash=hash_password(password),
        )
        return self.repository.create(user)

    def login(self, email: str, password: str) -> str:
        user = self.repository.get_by_email(email)

        if user is None:
            burn_password_check(password)
            raise UnauthorizedError("Incorrect email or password.")
        if not verify_password(password, user.password_hash):
            raise UnauthorizedError("Incorrect email or password.")
        if not user.is_active:
            raise UnauthorizedError("This account has been deactivated.")

        return create_access_token({"sub": str(user.id)})

    def update_profile(self, user: User, full_name: str) -> User:
        user.full_name = full_name
        self.repository.commit()
        self.repository.db.refresh(user)
        return user

    def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, user.password_hash):
            raise AppError("Your current password is incorrect.", code="wrong_password")
        user.password_hash = hash_password(new_password)
        self.repository.commit()
