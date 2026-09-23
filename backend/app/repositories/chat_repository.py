from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.chat_history import ChatHistory


class ChatRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_cached_answer(
        self,
        user_id: UUID,
        subject_id: UUID,
        normalized_question: str,
        newer_than: datetime | None = None,
    ) -> ChatHistory | None:
        """Exact-match answer cache.

        ``newer_than`` (the last time the subject's documents changed) prevents
        serving answers that were generated before new material was uploaded.
        """
        query = self.db.query(ChatHistory).filter(
            ChatHistory.user_id == user_id,
            ChatHistory.subject_id == subject_id,
            ChatHistory.normalized_question == normalized_question,
        )
        if newer_than is not None:
            query = query.filter(ChatHistory.created_at > newer_than)
        return query.order_by(ChatHistory.created_at.desc()).first()

    def create(self, chat: ChatHistory) -> ChatHistory:
        self.db.add(chat)
        self.db.commit()
        self.db.refresh(chat)
        return chat

    def replace_same_question(self, chat: ChatHistory) -> ChatHistory:
        """Insert ``chat`` and drop older rows with the same (normalized) question."""
        try:
            (
                self.db.query(ChatHistory)
                .filter(
                    ChatHistory.user_id == chat.user_id,
                    ChatHistory.subject_id == chat.subject_id,
                    ChatHistory.normalized_question == chat.normalized_question,
                )
                .delete(synchronize_session=False)
            )
            self.db.add(chat)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(chat)
        return chat

    def list_history(self, user_id: UUID, subject_id: UUID, limit: int = 50) -> list[ChatHistory]:
        rows = (
            self.db.query(ChatHistory)
            .filter(ChatHistory.user_id == user_id, ChatHistory.subject_id == subject_id)
            .order_by(ChatHistory.created_at.desc())
            .limit(limit)
            .all()
        )
        return rows[::-1]

    def clear(self, user_id: UUID, subject_id: UUID) -> int:
        deleted = (
            self.db.query(ChatHistory)
            .filter(ChatHistory.user_id == user_id, ChatHistory.subject_id == subject_id)
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return deleted
