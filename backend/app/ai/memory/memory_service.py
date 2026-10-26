from uuid import UUID

from sqlalchemy.orm import Session

from app.models.chat_history import ChatHistory


class MemoryService:
    def __init__(self, db: Session):
        self.db = db

    def get_recent_history(self, user_id: UUID, subject_id: UUID, limit: int = 5) -> list[ChatHistory]:
        rows = (
            self.db.query(ChatHistory)
            .filter(
                ChatHistory.user_id == user_id,
                ChatHistory.subject_id == subject_id,
            )
            .order_by(ChatHistory.created_at.desc())
            .limit(limit)
            .all()
        )
        return rows[::-1]
