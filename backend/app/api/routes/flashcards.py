from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.core.rate_limit import user_rate_limit
from app.database.session import get_db
from app.models.user import User
from app.schemas.flashcard import FlashcardResponse, FlashcardUpdate, GenerateFlashcardsResponse
from app.services.flashcard_service import FlashcardService

router = APIRouter(prefix="/flashcards", tags=["Flashcards"])

_limit = user_rate_limit("generate", lambda: settings.GENERATION_RATE_LIMIT_PER_MINUTE)


@router.post("/generate/{subject_id}", response_model=GenerateFlashcardsResponse, dependencies=[Depends(_limit)])
def generate_flashcards(
    subject_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return FlashcardService(db).generate(current_user.id, subject_id)


@router.get("/{subject_id}", response_model=list[FlashcardResponse])
def get_flashcards(
    subject_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return FlashcardService(db).get_flashcards(current_user.id, subject_id)


@router.patch("/item/{flashcard_id}", response_model=FlashcardResponse)
def update_flashcard(
    flashcard_id: UUID,
    payload: FlashcardUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a flashcard as mastered / not mastered."""
    return FlashcardService(db).set_mastered(current_user.id, flashcard_id, payload.mastered)
