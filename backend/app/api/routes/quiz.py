from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.repositories.quiz_repository import QuizRepository
from app.schemas.quiz import (
    QuizResponse,
    GenerateQuizResponse,
)
from app.services.quiz_service import QuizService


router = APIRouter(
    prefix="/quiz",
    tags=["Quiz"],
)


@router.post(
    "/generate/{subject_id}",
    response_model=GenerateQuizResponse,
)
def generate_quiz(
    subject_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = QuizService(
        QuizRepository(db)
    )

    return service.generate(
        user_id=current_user.id,
        subject_id=subject_id,
    )


@router.get(
    "/{subject_id}",
    response_model=list[QuizResponse],
)
def get_quizzes(
    subject_id: UUID,
    db: Session = Depends(get_db),
):

    service = QuizService(
        QuizRepository(db)
    )

    return service.get_quizzes(
        subject_id,
    )