from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentResponse
from app.services.document_service import DocumentService

from app.models.user import User
from app.auth.dependencies import get_current_user
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentResponse
from app.services.document_service import DocumentService

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "/upload/{subject_id}",
    response_model=DocumentResponse,
)
async def upload_document(
    subject_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = DocumentService(
        DocumentRepository(db)
    )

    return await service.upload(
        file,
        subject_id,
        current_user,
    )


@router.get(
    "/{subject_id}",
    response_model=list[DocumentResponse],
)
def get_documents(
    subject_id: UUID,
    db: Session = Depends(get_db),
):

    service = DocumentService(
        DocumentRepository(db)
    )

    return service.get_documents(subject_id)


@router.get(
    "",
    response_model=list[DocumentResponse],
)
def get_all_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    service = DocumentService(
        DocumentRepository(db)
    )

    return service.get_all_documents(
        current_user.id
    )