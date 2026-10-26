import mimetypes
from uuid import UUID

from fastapi import APIRouter, Depends, File, Response, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload/{subject_id}", response_model=DocumentResponse)
async def upload_document(
    subject_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Store the file and queue it for processing. Poll the list endpoints for `status`."""
    return await DocumentService(db).upload(file, subject_id, current_user)


@router.get("", response_model=list[DocumentResponse])
def get_all_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return DocumentService(db).list_all(current_user.id)


@router.get("/{subject_id}", response_model=list[DocumentResponse])
def get_documents(
    subject_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return DocumentService(db).list_for_subject(current_user.id, subject_id)


@router.get("/{document_id}/status", response_model=DocumentResponse)
def get_document_status(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return DocumentService(db).get(current_user.id, document_id)


@router.get("/{document_id}/file")
def open_document_file(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    path, document = DocumentService(db).file_path(current_user.id, document_id)
    media_type = mimetypes.guess_type(document.original_filename)[0] or "application/octet-stream"
    return FileResponse(
        path,
        media_type=media_type,
        filename=document.original_filename,
        content_disposition_type="inline" if document.file_type in ("pdf", "txt") else "attachment",
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.post("/{document_id}/reindex", response_model=DocumentResponse)
def reindex_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return DocumentService(db).reindex(current_user.id, document_id)


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    DocumentService(db).delete(current_user.id, document_id)
    return Response(status_code=204)
