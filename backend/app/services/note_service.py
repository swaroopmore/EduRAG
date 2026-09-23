from uuid import UUID

from app.ai.parser import NoteParser
from app.ai.prompts.note_prompt import NOTES_SYSTEM_PROMPT, NOTES_USER_PROMPT
from app.models.note import Note
from app.repositories.note_repository import NoteRepository
from app.services.generation_base import BaseGenerationService


class NoteService(BaseGenerationService):
    kind = "notes"
    parser = NoteParser
    repository_cls = NoteRepository

    def build_prompts(self, material: str, **_) -> tuple[str, str]:
        return NOTES_SYSTEM_PROMPT, NOTES_USER_PROMPT.format(context=material)

    def to_models(self, items, user_id: UUID, subject_id: UUID) -> list[Note]:
        return [
            Note(title=i.title, content=i.content, keywords=i.keywords, user_id=user_id, subject_id=subject_id)
            for i in items
        ]

    def get_notes(self, user_id: UUID, subject_id: UUID):
        return self.list(user_id, subject_id)
