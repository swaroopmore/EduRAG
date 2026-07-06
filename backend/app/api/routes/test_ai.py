from fastapi import APIRouter

from app.ai.llm.gemini_service import GeminiService

router = APIRouter(
    prefix="/test-ai",
    tags=["AI"],
)


@router.get("/")
def test_ai():

    llm = GeminiService()

    answer = llm.generate(
        "Explain Python in one sentence."
    )

    return {
        "answer": answer
    }