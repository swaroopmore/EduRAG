from app.models.subject import Subject
from app.repositories.base_repository import BaseRepository


class SubjectRepository(BaseRepository[Subject]):

    def __init__(self, db):
        super().__init__(Subject, db)

    def get_by_user(self, user_id):
        return (
            self.db.query(Subject)
            .filter(Subject.user_id == user_id)
            .all()
        )