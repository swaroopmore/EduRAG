from uuid import UUID

from sqlalchemy.orm import Session

from app.models.note import Note


class NoteRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def create_many(
        self,
        notes: list[Note],
    ):

        self.db.add_all(notes)

        self.db.commit()

        return notes

    def get_by_subject(
        self,
        subject_id: UUID,
    ):

        return (
            self.db.query(Note)
            .filter(
                Note.subject_id == subject_id
            )
            .order_by(
                Note.created_at.desc()
            )
            .all()
        )

    def delete_by_subject(
        self,
        subject_id: UUID,
    ):

        (
            self.db.query(Note)
            .filter(
                Note.subject_id == subject_id
            )
            .delete()
        )

        self.db.commit()

    def delete(
        self,
        note_id: UUID,
    ):

        note = (
            self.db.query(Note)
            .filter(
                Note.id == note_id
            )
            .first()
        )

        if note:

            self.db.delete(note)

            self.db.commit()

        return note