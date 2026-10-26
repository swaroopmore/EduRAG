from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.core.rate_limit import user_rate_limit
from app.database.session import get_db
from app.models.user import User
from app.schemas.note import GenerateNotesResponse, NoteResponse
from app.services.note_service import NoteService

router = APIRouter(prefix="/notes", tags=["Notes"])

_limit = user_rate_limit("generate", lambda: settings.GENERATION_RATE_LIMIT_PER_MINUTE)


@router.post("/generate/{subject_id}", response_model=GenerateNotesResponse, dependencies=[Depends(_limit)])
def generate_notes(
    subject_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """(Re)generate the subject's notes. Existing notes are replaced atomically."""
    return NoteService(db).generate(current_user.id, subject_id)


@router.get("/{subject_id}", response_model=list[NoteResponse])
def get_notes(
    subject_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return NoteService(db).get_notes(current_user.id, subject_id)
