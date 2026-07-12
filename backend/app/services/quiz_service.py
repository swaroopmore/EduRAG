from uuid import UUID

from app.ai.llm.gemini_service import GeminiService
from app.ai.parser.quiz_parser import QuizParser
from app.ai.prompts.quiz_prompt import QUIZ_PROMPT
from app.ai.retrieval.retriever import Retriever
from app.models.quiz import Quiz
from app.repositories.quiz_repository import QuizRepository


class QuizService:

    def __init__(
        self,
        repository: QuizRepository,
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
            question="Generate quiz",
            user_id=user_id,
            subject_id=subject_id,
        )

        context = "\n\n".join(
            doc.page_content
            for doc in docs
        )

        prompt = QUIZ_PROMPT.format(
            context=context,
        )

        response = self.llm.generate(
            prompt,
        )

        quizzes = QuizParser.parse(
            response,
        )

        self.repository.delete_by_subject(
            subject_id,
        )

        quiz_objects = []

        for quiz in quizzes:

            quiz_objects.append(
                Quiz(
                    question=quiz["question"],
                    option_a=quiz["option_a"],
                    option_b=quiz["option_b"],
                    option_c=quiz["option_c"],
                    option_d=quiz["option_d"],
                    correct_answer=quiz["correct_answer"],
                    explanation=quiz["explanation"],
                    user_id=user_id,
                    subject_id=subject_id,
                )
            )

        self.repository.create_many(
            quiz_objects,
        )

        return {
            "generated": len(quiz_objects)
        }

    def get_quizzes(
        self,
        subject_id: UUID,
    ):

        return self.repository.get_by_subject(
            subject_id,
        )