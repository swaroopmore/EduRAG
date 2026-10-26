from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.vectorstore.chroma_service import get_vectorstore
from app.core.errors import AppError, ConflictError
from app.core.logging import get_logger, short_id
from app.models.subject import Subject
from app.repositories.document_repository import DocumentRepository
from app.repositories.subject_repository import SubjectRepository
from app.schemas.subject import SubjectResponse
from app.services.access import require_subject
from app.services.storage_service import StorageService

logger = get_logger("subjects")


class SubjectService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = SubjectRepository(db)

    def _response(self, subject: Subject, counts: dict | None = None) -> SubjectResponse:
        counts = counts or {}
        return SubjectResponse(
            id=subject.id,
            name=subject.name,
            description=subject.description,
            created_at=subject.created_at,
            updated_at=subject.updated_at,
            document_count=counts.get("documents", 0),
            ready_document_count=counts.get("documents_ready", 0),
            note_count=counts.get("notes", 0),
            flashcard_count=counts.get("flashcards", 0),
            quiz_question_count=counts.get("quiz_questions", 0),
            study_session_count=counts.get("study_sessions", 0),
        )

    def create(self, name: str, description: str | None, user_id: UUID) -> SubjectResponse:
        if self.repository.name_exists(user_id, name):
            raise ConflictError("You already have a subject with this name.", code="subject_exists")
        subject = self.repository.create(Subject(name=name, description=description, user_id=user_id))
        return self._response(subject)

    def get_all(self, user_id: UUID) -> list[SubjectResponse]:
        counts = self.repository.counts_by_subject(user_id)
        return [self._response(s, counts.get(s.id)) for s in self.repository.get_by_user(user_id)]

    def get(self, user_id: UUID, subject_id: UUID) -> SubjectResponse:
        subject = require_subject(self.db, user_id, subject_id)
        counts = self.repository.counts_by_subject(user_id)
        return self._response(subject, counts.get(subject.id))

    def update(self, user_id: UUID, subject_id: UUID, name: str, description: str | None) -> SubjectResponse:
        subject = require_subject(self.db, user_id, subject_id)
        if self.repository.name_exists(user_id, name, exclude_id=subject.id):
            raise ConflictError("You already have a subject with this name.", code="subject_exists")
        subject.name = name
        subject.description = description
        self.repository.commit()
        self.db.refresh(subject)
        return self._response(subject, self.repository.counts_by_subject(user_id).get(subject.id))

    def delete(self, user_id: UUID, subject_id: UUID) -> None:
        """Delete a subject and everything derived from it (rows, vectors, files)."""
        subject = require_subject(self.db, user_id, subject_id)
        documents = DocumentRepository(self.db).paths_for_subject(subject.id, user_id)
        try:
            get_vectorstore().delete_subject(user_id, subject.id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("vector cleanup failed for subject %s", short_id(subject_id))
            raise AppError(
                "We couldn't delete this subject right now. Please try again.", code="delete_failed"
            ) from exc

        storage = StorageService()
        for document in documents:
            storage.delete(document)
        self.repository.delete(subject)  # ON DELETE CASCADE removes notes, quizzes, chats...
        logger.info("deleted subject=%s user=%s documents=%d", short_id(subject_id), short_id(user_id), len(documents))
