from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.repositories.flashcard_repository import FlashcardRepository
from app.schemas.flashcard import (
    FlashcardResponse,
    GenerateFlashcardsResponse,
)
from app.services.flashcard_service import FlashcardService

router = APIRouter(
    prefix="/flashcards",
    tags=["Flashcards"],
)


@router.post(
    "/generate/{subject_id}",
    response_model=GenerateFlashcardsResponse,
)
def generate_flashcards(
    subject_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = FlashcardService(
        FlashcardRepository(db)
    )

    return service.generate(
        user_id=current_user.id,
        subject_id=subject_id,
    )


@router.get(
    "/{subject_id}",
    response_model=list[FlashcardResponse],
)
def get_flashcards(
    subject_id: UUID,
    db: Session = Depends(get_db),
):

    service = FlashcardService(
        FlashcardRepository(db)
    )

    return service.get_flashcards(
        subject_id,
    )