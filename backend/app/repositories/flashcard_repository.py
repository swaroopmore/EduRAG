from app.models.flashcard import Flashcard
from app.repositories.subject_resource_repository import SubjectResourceRepository


class FlashcardRepository(SubjectResourceRepository[Flashcard]):
    model = Flashcard
    order_by = (Flashcard.created_at.asc(),)
