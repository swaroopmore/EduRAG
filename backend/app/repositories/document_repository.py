from app.models.document import Document
from app.repositories.base_repository import BaseRepository


class DocumentRepository(BaseRepository[Document]):

    def __init__(self, db):
        super().__init__(Document, db)