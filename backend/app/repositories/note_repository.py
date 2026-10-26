from app.models.note import Note
from app.repositories.subject_resource_repository import SubjectResourceRepository


class NoteRepository(SubjectResourceRepository[Note]):
    model = Note
    order_by = (Note.created_at.asc(),)
