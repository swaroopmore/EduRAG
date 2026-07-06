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

        history = self.memory.get_history(user_id)

        history_text = "\n".join(
            f"{msg['role']}: {msg['content']}"
            for msg in history
        )

        normalized = normalize_question(question)

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

        docs = self.retriever.retrieve(
            question=question,
            user_id=user_id,
            subject_id=subject_id,
        )

        context = "\n\n".join(
            doc.page_content
            for doc in docs
        )

        prompt = TEACHER_PROMPT.format(
            history=history_text,
            context=context,
            question=question,
        )

        answer = self.llm.generate(prompt)

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

        citations = []

        for doc in docs:

            citations.append(
                {
                    "document": doc.metadata.get("filename"),
                    "page": doc.metadata.get("page", 0) + 1,
                    "snippet": doc.page_content[:250],
                }
            )

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