from uuid import UUID

from app.ai.llm.gemini_service import GeminiService
from app.ai.parser.flashcard_parser import FlashcardParser
from app.ai.prompts.flashcard_prompt import FLASHCARD_PROMPT
from app.ai.retrieval.retriever import Retriever
from app.models.flashcard import Flashcard
from app.repositories.flashcard_repository import FlashcardRepository


class FlashcardService:

    def __init__(
        self,
        repository: FlashcardRepository,
    ):

        self.repository = repository

        self.retriever = Retriever()

        self.llm = GeminiService()

    def generate(
        self,
        user_id: UUID,
        subject_id: UUID,
    ):

        docs = self.retriever.retrieve(
            question="Generate flashcards",
            user_id=user_id,
            subject_id=subject_id,
        )

        context = "\n\n".join(
            doc.page_content
            for doc in docs
        )

        prompt = FLASHCARD_PROMPT.format(
            context=context,
        )

        response = self.llm.generate(
            prompt,
        )

        flashcards = FlashcardParser.parse(
            response,
        )

        self.repository.delete_by_subject(
            subject_id,
        )

        cards = []

        for card in flashcards:

            cards.append(
                Flashcard(
                    question=card["question"],
                    answer=card["answer"],
                    user_id=user_id,
                    subject_id=subject_id,
                )
            )

        self.repository.create_many(
            cards,
        )

        return {
            "generated": len(cards)
        }

    def get_flashcards(
        self,
        subject_id: UUID,
    ):

        return self.repository.get_by_subject(
            subject_id,
        )