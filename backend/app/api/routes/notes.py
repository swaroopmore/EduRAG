from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.repositories.note_repository import NoteRepository
from app.schemas.note import (
    NoteResponse,
    GenerateNotesResponse,
)
from app.services.note_service import NoteService


router = APIRouter(
    prefix="/notes",
    tags=["Notes"],
)


@router.post(
    "/generate/{subject_id}",
    response_model=GenerateNotesResponse,
)
def generate_notes(
    subject_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = NoteService(
        NoteRepository(db)
    )

    return service.generate(
        user_id=current_user.id,
        subject_id=subject_id,
    )


@router.get(
    "/{subject_id}",
    response_model=list[NoteResponse],
)
def get_notes(
    subject_id: UUID,
    db: Session = Depends(get_db),
):

    service = NoteService(
        NoteRepository(db)
    )

    return service.get_notes(
        subject_id,
    )