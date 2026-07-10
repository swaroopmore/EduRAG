from uuid import UUID

from sqlalchemy.orm import Session

from app.models.document import Document


class DocumentRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        document: Document,
    ):

        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        return document

    def get_documents_by_subject(
        self,
        subject_id: UUID,
    ):

        return (
            self.db.query(Document)
            .filter(Document.subject_id == subject_id)
            .order_by(Document.created_at.desc())
            .all()
        )