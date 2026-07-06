from sqlalchemy.orm import Session

from app.models.chat_history import ChatHistory


class ChatRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_cached_answer(
        self,
        user_id,
        subject_id,
        normalized_question,
    ):
        return (
            self.db.query(ChatHistory)
            .filter(
                ChatHistory.user_id == user_id,
                ChatHistory.subject_id == subject_id,
                ChatHistory.normalized_question == normalized_question,
            )
            .first()
        )

    def create(
        self,
        chat: ChatHistory,
    ):
        self.db.add(chat)
        self.db.commit()
        self.db.refresh(chat)
        return chat