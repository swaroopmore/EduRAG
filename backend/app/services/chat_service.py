from sqlalchemy.orm import Session

from app.ai.llm.gemini_service import GeminiService
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
        self.memory = MemoryService()

    def ask(
        self,
        question,
        user_id,
        subject_id,
    ):

        # -----------------------------
        # Get Conversation History
        # -----------------------------
        history = self.memory.get_history(user_id)

        history_text = "\n".join(
            f"{msg['role']}: {msg['content']}"
            for msg in history
        )

        # -----------------------------
        # Normalize Question
        # -----------------------------
        normalized = normalize_question(question)

        # -----------------------------
        # Cache Lookup
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
                "sources": cached.sources,
            }

        print("❌ CACHE MISS")

        # -----------------------------
        # Retrieve Relevant Chunks
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
        # Build Prompt
        # -----------------------------
        prompt = TEACHER_PROMPT.format(
            history=history_text,
            context=context,
            question=question,
        )

        # -----------------------------
        # Gemini Response
        # -----------------------------
        answer = self.llm.generate(prompt)

        # -----------------------------
        # Save Conversation in Memory
        # -----------------------------
        self.memory.add_message(
            user_id,
            "user",
            question,
        )

        self.memory.add_message(
            user_id,
            "assistant",
            answer,
        )

        # -----------------------------
        # Extract Sources
        # -----------------------------
        sources = list(
            {
                doc.metadata.get("filename")
                for doc in docs
            }
        )

        # -----------------------------
        # Save Chat History
        # -----------------------------
        chat = ChatHistory(
            user_id=user_id,
            subject_id=subject_id,
            question=question,
            normalized_question=normalized,
            answer=answer,
            sources=sources,
        )

        self.repository.create(chat)

        # -----------------------------
        # Return Response
        # -----------------------------
        return {
            "answer": answer,
            "sources": sources,
        }