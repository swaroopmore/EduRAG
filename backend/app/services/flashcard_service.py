from uuid import UUID

from app.ai.parser import FlashcardParser
from app.ai.prompts.flashcard_prompt import FLASHCARD_SYSTEM_PROMPT, FLASHCARD_USER_PROMPT
from app.core.errors import NotFoundError
from app.models.flashcard import Flashcard
from app.repositories.flashcard_repository import FlashcardRepository
from app.services.generation_base import BaseGenerationService


class FlashcardService(BaseGenerationService):
    kind = "flashcards"
    parser = FlashcardParser
    repository_cls = FlashcardRepository

    def build_prompts(self, material: str, **_) -> tuple[str, str]:
        return FLASHCARD_SYSTEM_PROMPT, FLASHCARD_USER_PROMPT.format(context=material)

    def to_models(self, items, user_id: UUID, subject_id: UUID) -> list[Flashcard]:
        return [
            Flashcard(question=i.question, answer=i.answer, user_id=user_id, subject_id=subject_id)
            for i in items
        ]

    def get_flashcards(self, user_id: UUID, subject_id: UUID):
        return self.list(user_id, subject_id)

    def set_mastered(self, user_id: UUID, flashcard_id: UUID, mastered: bool) -> Flashcard:
        card = self.repository.get_owned(flashcard_id, user_id)
        if card is None:
            raise NotFoundError("Flashcard not found.")
        card.mastered = mastered
        self.repository.commit()
        self.db.refresh(card)
        return card
