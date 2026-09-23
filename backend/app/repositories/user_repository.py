import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> User | None:
        return (
            self.db.query(User)
            .filter(func.lower(User.email) == email.strip().lower())
            .first()
        )

    def get_by_id(self, user_id) -> User | None:  # type: ignore[override]
        try:
            parsed = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
        except ValueError:
            return None
        return self.db.query(User).filter(User.id == parsed).first()
