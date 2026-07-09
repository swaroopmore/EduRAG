from sqlalchemy.orm import Session

from app.models.chat_history import ChatHistory


class MemoryService:

    def __init__(self, db: Session):
        self.db = db

    def get_recent_history(
        self,
        user_id,
        subject_id,
        limit: int = 5,
    ):

        return (
            self.db.query(ChatHistory)
            .filter(
                ChatHistory.user_id == user_id,
                ChatHistory.subject_id == subject_id,
            )
            .order_by(ChatHistory.created_at.desc())
            .limit(limit)
            .all()[::-1]
        )