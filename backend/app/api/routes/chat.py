from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.core.rate_limit import user_rate_limit
from app.database.session import get_db, session_scope
from app.models.user import User
from app.schemas.chat import ChatHistoryItem, ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["AI Teacher"])

_chat_limit = user_rate_limit("chat", lambda: settings.CHAT_RATE_LIMIT_PER_MINUTE)


@router.post("/ask", response_model=ChatResponse, dependencies=[Depends(_chat_limit)])
def ask(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ChatService(db).ask(current_user.id, request)


@router.post("/stream", dependencies=[Depends(_chat_limit)])
def ask_stream(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """Server-sent events variant of /ask (events: start, token, done, error)."""
    user_id = current_user.id

    def events():
        # The generator owns its DB session; request-scoped sessions may be closed
        # before a streaming body finishes.
        with session_scope() as db:
            yield from ChatService(db).stream(user_id, request)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/history/{subject_id}", response_model=list[ChatHistoryItem])
def history(
    subject_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ChatService(db).history(current_user.id, subject_id, limit)


@router.delete("/history/{subject_id}", status_code=204)
def clear_history(
    subject_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ChatService(db).clear_history(current_user.id, subject_id)
    return Response(status_code=204)
