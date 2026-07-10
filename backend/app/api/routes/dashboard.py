from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("")
def dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return {
        "full_name": current_user.full_name,
        "subjects": 0,
        "documents": 0,
        "ai_chats": 0,
        "flashcards": 0,
        "quizzes": 0,
    }