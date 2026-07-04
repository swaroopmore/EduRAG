from app.ai.llm.gemini_service import GeminiService
from app.ai.prompts.teacher_prompt import TEACHER_PROMPT
from app.ai.rag.retriever import Retriever


class ChatService:

    def __init__(self):

        self.retriever = Retriever()
        self.llm = GeminiService()

    def ask(
        self,
        question,
        user_id,
        subject_id,
    ):

        docs = self.retriever.retrieve(
            question,
            user_id,
            subject_id,
        )

        context = "\n\n".join(
            doc.page_content
            for doc in docs
        )

        prompt = TEACHER_PROMPT.format(
            context=context,
            question=question,
        )

        answer = self.llm.generate(prompt)

        return {
            "answer": answer,
            "sources": [
                doc.metadata.get("filename")
                for doc in docs
            ]
        }