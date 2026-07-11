from uuid import UUID

from fastapi import UploadFile

from app.ai.pipeline.document_pipeline import DocumentPipeline
from app.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.services.storage_service import StorageService


class DocumentService:

    def __init__(
        self,
        repository: DocumentRepository,
    ):
        self.repository = repository
        self.storage = StorageService()

    async def upload(
        self,
        file: UploadFile,
        subject_id,
        current_user,
    ):

        # Save file to disk
        uploaded = await self.storage.save_file(file)

        # Save document metadata
        document = Document(
            filename=uploaded["filename"],
            original_filename=file.filename,
            file_type=uploaded["type"],
            file_size=uploaded["size"],
            file_path=uploaded["path"],
            subject_id=subject_id,
        )

        # Save to PostgreSQL
        document = self.repository.create(document)

        # Create pipeline only for uploads
        pipeline = DocumentPipeline()

        # Process document
        pipeline.process(
            uploaded["path"],
            uploaded["type"],
            document,
            current_user,
        )

        return document

    def get_documents(
        self,
        subject_id: UUID,
    ):
        return self.repository.get_documents_by_subject(
            subject_id
        )