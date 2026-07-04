from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(
    prefix="/chat",
    tags=["AI Teacher"],
)


@router.post(
    "/ask",
    response_model=ChatResponse,
)
def ask_question(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):

    service = ChatService()

    return service.ask(
        question=request.question,
        user_id=current_user.id,
        subject_id=request.subject_id,
    )