from sqlalchemy.orm import Session

from app.ai.llm.gemini_service import GeminiService
from app.ai.memory.formatter import ConversationFormatter
from app.ai.memory.memory_service import MemoryService
from app.ai.prompts.teacher_prompt import TEACHER_PROMPT
from app.ai.retrieval.retriever import Retriever
from app.models.chat_history import ChatHistory
from app.repositories.chat_repository import ChatRepository
from app.utils.text import normalize_question


class ChatService:

    def __init__(self, db: Session):

        self.repository = ChatRepository(db)
        self.retriever = Retriever()
        self.llm = GeminiService()

        # Database-backed conversation memory
        self.memory = MemoryService(db)

    def ask(
        self,
        question,
        user_id,
        subject_id,
    ):

        # -----------------------------
        # Fetch previous conversation
        # -----------------------------
        history = self.memory.get_recent_history(
            user_id=user_id,
            subject_id=subject_id,
            limit=5,
        )

        history_text = ConversationFormatter.format(history)

        normalized = normalize_question(question)

        # -----------------------------
        # Exact cache
        # -----------------------------
        cached = self.repository.get_cached_answer(
            user_id=user_id,
            subject_id=subject_id,
            normalized_question=normalized,
        )

        if cached:

            print("✅ CACHE HIT")

            return {
                "answer": cached.answer,
                "citations": cached.citations,
            }

        print("❌ CACHE MISS")

        # -----------------------------
        # Retrieve documents
        # -----------------------------
        docs = self.retriever.retrieve(
            question=question,
            user_id=user_id,
            subject_id=subject_id,
        )

        context = "\n\n".join(
            doc.page_content
            for doc in docs
        )

        # -----------------------------
        # Build prompt
        # -----------------------------
        prompt = TEACHER_PROMPT.format(
            history=history_text,
            context=context,
            question=question,
        )

        # -----------------------------
        # Generate answer
        # -----------------------------
        answer = self.llm.generate(prompt)

        # -----------------------------
        # Build citations
        # -----------------------------
        citations = []

        for doc in docs:

            citations.append(
                {
                    "document": doc.metadata.get("filename"),
                    "page": doc.metadata.get("page", 0) + 1,
                    "snippet": doc.page_content[:250],
                }
            )

        # -----------------------------
        # Save conversation
        # -----------------------------
        chat = ChatHistory(
            user_id=user_id,
            subject_id=subject_id,
            question=question,
            normalized_question=normalized,
            answer=answer,
            citations=citations,
        )

        self.repository.create(chat)

        return {
            "answer": answer,
            "citations": citations,
        }