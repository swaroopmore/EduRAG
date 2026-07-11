from uuid import UUID

from sqlalchemy.orm import Session

from app.models.flashcard import Flashcard


class FlashcardRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        flashcard: Flashcard,
    ):

        self.db.add(flashcard)

        self.db.commit()

        self.db.refresh(flashcard)

        return flashcard

    def create_many(
        self,
        flashcards: list[Flashcard],
    ):

        self.db.add_all(flashcards)

        self.db.commit()

        return flashcards

    def get_by_subject(
        self,
        subject_id: UUID,
    ):

        return (
            self.db.query(Flashcard)
            .filter(
                Flashcard.subject_id == subject_id
            )
            .order_by(
                Flashcard.created_at.desc()
            )
            .all()
        )

    def delete_by_subject(
        self,
        subject_id: UUID,
    ):

        (
            self.db.query(Flashcard)
            .filter(
                Flashcard.subject_id == subject_id
            )
            .delete()
        )

        self.db.commit()

    def delete(
        self,
        flashcard_id: UUID,
    ):

        flashcard = (
            self.db.query(Flashcard)
            .filter(
                Flashcard.id == flashcard_id
            )
            .first()
        )

        if flashcard:

            self.db.delete(flashcard)

            self.db.commit()

        return flashcard