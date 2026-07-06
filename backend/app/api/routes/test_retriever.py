from uuid import UUID

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.ai.retrieval.retriever import Retriever
from app.models.user import User

router = APIRouter(
    prefix="/test-retriever",
    tags=["AI"],
)


@router.get("/")
def test_retriever(
    subject_id: UUID,
    question: str,
    current_user: User = Depends(get_current_user),
):

    retriever = Retriever()

    docs = retriever.retrieve(
        question=question,
        user_id=current_user.id,
        subject_id=subject_id,
    )

    return [
        {
            "content": doc.page_content,
            "metadata": doc.metadata,
        }
        for doc in docs
    ]