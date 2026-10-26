from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.core.rate_limit import user_rate_limit
from app.database.session import get_db
from app.models.user import User
from app.schemas.quiz import (
    GenerateQuizResponse,
    QuizAttemptResponse,
    QuizAttemptSummary,
    QuizQuestionResponse,
    QuizSubmission,
)
from app.services.quiz_service import QuizService

router = APIRouter(prefix="/quiz", tags=["Quiz"])

_limit = user_rate_limit("generate", lambda: settings.GENERATION_RATE_LIMIT_PER_MINUTE)


@router.post("/generate/{subject_id}", response_model=GenerateQuizResponse, dependencies=[Depends(_limit)])
def generate_quiz(
    subject_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return QuizService(db).generate(current_user.id, subject_id)


@router.get("/{subject_id}", response_model=list[QuizQuestionResponse])
def get_quizzes(
    subject_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Questions without answers - grading happens on submission."""
    return QuizService(db).get_quizzes(current_user.id, subject_id)


@router.post("/{subject_id}/attempts", response_model=QuizAttemptResponse)
def submit_quiz(
    subject_id: UUID,
    submission: QuizSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return QuizService(db).submit(current_user.id, subject_id, submission)


@router.get("/{subject_id}/attempts", response_model=list[QuizAttemptSummary])
def list_quiz_attempts(
    subject_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return QuizService(db).attempts(current_user.id, subject_id)
