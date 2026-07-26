from uuid import UUID

from app.ai.llm.gemini_service import GeminiService
from app.ai.parser.note_parser import NoteParser
from app.ai.prompts.note_prompt import NOTES_PROMPT
from app.ai.retrieval.retriever import Retriever
from app.models.note import Note
from app.repositories.note_repository import NoteRepository


class NoteService:

    def __init__(
        self,
        repository: NoteRepository,
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
            question="Generate study notes",
            user_id=user_id,
            subject_id=subject_id,
        )

        print(f"Retrieved {len(docs)} documents")

        # No documents found
        if not docs:
            return {
                "generated": 0,
                "message": "No documents found for this subject."
            }

        context = "\n\n".join(
            doc.page_content
            for doc in docs
        )

        prompt = NOTES_PROMPT.format(
            context=context,
        )

        response = self.llm.generate(
            prompt,
        )

        print("Gemini Response:")
        print(response)

        if not response or not response.strip():
            raise Exception(
                "Gemini returned an empty response."
            )

        try:
            notes = NoteParser.parse(
                response,
            )
        except Exception as e:
            print("Failed to parse notes:", e)
            print(response)
            raise

        self.repository.delete_by_subject(
            subject_id,
        )

        note_objects = []

        for note in notes:

            note_objects.append(

                Note(
                    title=note.get("title", ""),
                    content=note.get("content", ""),
                    user_id=user_id,
                    subject_id=subject_id,
                )

            )

        if note_objects:

            self.repository.create_many(
                note_objects,
            )

        return {

            "generated": len(note_objects)

        }

    def get_notes(
        self,
        subject_id: UUID,
    ):

        return self.repository.get_by_subject(
            subject_id,
        )