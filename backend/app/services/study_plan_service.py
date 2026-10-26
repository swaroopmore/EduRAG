from uuid import UUID

from app.ai.parser import StudyPlanParser
from app.ai.prompts.study_plan_prompt import STUDY_PLAN_SYSTEM_PROMPT, STUDY_PLAN_USER_PROMPT
from app.core.errors import NotFoundError
from app.models.study_plan import StudyPlan
from app.repositories.study_plan_repository import StudyPlanRepository
from app.services.generation_base import BaseGenerationService


class StudyPlanService(BaseGenerationService):
    kind = "study_plan"
    parser = StudyPlanParser
    repository_cls = StudyPlanRepository

    def build_prompts(self, material: str, days: int = 7, **_) -> tuple[str, str]:
        return (
            STUDY_PLAN_SYSTEM_PROMPT.format(days=days),
            STUDY_PLAN_USER_PROMPT.format(context=material, days=days),
        )

    def to_models(self, items, user_id: UUID, subject_id: UUID) -> list[StudyPlan]:
        return [
            StudyPlan(
                day=i.day, time=i.time, title=i.title, description=i.description,
                duration=i.duration, quote=i.quote or None, user_id=user_id, subject_id=subject_id,
            )
            for i in items
        ]

    def get_study_plan(self, user_id: UUID, subject_id: UUID):
        return self.list(user_id, subject_id)

    def set_completed(self, user_id: UUID, plan_id: UUID, completed: bool) -> StudyPlan:
        plan = self.repository.get_owned(plan_id, user_id)
        if plan is None:
            raise NotFoundError("Study session not found.")
        plan.completed = completed
        self.repository.commit()
        self.db.refresh(plan)
        return plan
