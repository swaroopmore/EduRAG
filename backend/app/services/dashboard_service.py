from uuid import UUID

from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import DashboardResponse


class DashboardService:

    def __init__(
        self,
        repository: DashboardRepository,
    ):

        self.repository = repository

    def get_dashboard(
        self,
        user_id: UUID,
    ) -> DashboardResponse:

        return DashboardResponse(

            subjects=self.repository.count_subjects(
                user_id
            ),

            documents=self.repository.count_documents(
                user_id
            ),

            flashcards=self.repository.count_flashcards(
                user_id
            ),

            quizzes=self.repository.count_quizzes(
                user_id
            ),

            notes=self.repository.count_notes(
                user_id
            ),

            study_plans=self.repository.count_study_plans(
                user_id
            ),

            storage_used=self.repository.storage_used(
                user_id
            ),

        )