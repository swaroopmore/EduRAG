from uuid import UUID

from app.ai.llm.gemini_service import GeminiService
from app.ai.parser.study_plan_parser import StudyPlanParser
from app.ai.prompts.study_plan_prompt import STUDY_PLAN_PROMPT
from app.ai.retrieval.retriever import Retriever
from app.models.study_plan import StudyPlan
from app.repositories.study_plan_repository import (
    StudyPlanRepository,
)


class StudyPlanService:

    def __init__(
        self,
        repository: StudyPlanRepository,
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
            question="Generate a study plan",
            user_id=user_id,
            subject_id=subject_id,
        )

        context = "\n\n".join(
            doc.page_content
            for doc in docs
        )

        prompt = STUDY_PLAN_PROMPT.format(
            context=context,
        )

        response = self.llm.generate(
            prompt,
        )

        plans = StudyPlanParser.parse(
            response,
        )

        self.repository.delete_by_subject(
            subject_id,
        )

        study_plans = []

        for plan in plans:

            study_plans.append(

                StudyPlan(

                    day=plan["day"],

                    time=plan["time"],

                    title=plan["title"],

                    description=plan["description"],

                    duration=plan["duration"],

                    user_id=user_id,

                    subject_id=subject_id,

                )

            )

        self.repository.create_many(
            study_plans,
        )

        return {

            "generated": len(
                study_plans
            )

        }

    def get_study_plan(
        self,
        subject_id: UUID,
    ):

        return self.repository.get_by_subject(
            subject_id,
        )