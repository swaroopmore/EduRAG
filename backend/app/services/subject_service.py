from app.models.subject import Subject
from app.repositories.subject_repository import SubjectRepository


class SubjectService:

    def __init__(self, repository: SubjectRepository):
        self.repository = repository

    def create(
        self,
        name,
        description,
        user_id,
    ):
        subject = Subject(
            name=name,
            description=description,
            user_id=user_id,
        )

        return self.repository.create(subject)

    def get_all(self, user_id):
        return self.repository.get_by_user(user_id)