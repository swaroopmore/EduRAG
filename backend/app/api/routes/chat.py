from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from sqlalchemy.orm import Session
from app.database.session import get_db

router = APIRouter(
    prefix="/chat",
    tags=["AI Teacher"],
)


@router.post("/ask")
def ask(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = ChatService(db)

    return service.ask(
        question=request.question,
        user_id=current_user.id,
        subject_id=request.subject_id,
    )