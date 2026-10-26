from uuid import UUID

from app.ai.parser import QuizParser
from app.ai.prompts.quiz_prompt import QUIZ_SYSTEM_PROMPT, QUIZ_USER_PROMPT
from app.core.errors import ConflictError
from app.models.quiz import Quiz, QuizAttempt
from app.repositories.quiz_repository import QuizRepository
from app.schemas.quiz import (
    QuizAttemptResponse,
    QuizAttemptSummary,
    QuizQuestionResult,
    QuizSubmission,
)
from app.services.access import require_subject
from app.services.generation_base import BaseGenerationService


def _accuracy(score: int, total: int) -> int:
    return round(100 * score / total) if total else 0


class QuizService(BaseGenerationService):
    kind = "quiz"
    parser = QuizParser
    repository_cls = QuizRepository

    def build_prompts(self, material: str, **_) -> tuple[str, str]:
        return QUIZ_SYSTEM_PROMPT, QUIZ_USER_PROMPT.format(context=material)

    def to_models(self, items, user_id: UUID, subject_id: UUID) -> list[Quiz]:
        return [
            Quiz(
                question=i.question, option_a=i.option_a, option_b=i.option_b,
                option_c=i.option_c, option_d=i.option_d, correct_answer=i.correct_answer,
                explanation=i.explanation or "", user_id=user_id, subject_id=subject_id,
            )
            for i in items
        ]

    def get_quizzes(self, user_id: UUID, subject_id: UUID):
        return self.list(user_id, subject_id)

    # ----------------------------------------------------------------- grading
    def submit(self, user_id: UUID, subject_id: UUID, submission: QuizSubmission) -> QuizAttemptResponse:
        """Grade on the server so correct answers are only revealed after submission."""
        require_subject(self.db, user_id, subject_id)
        questions = self.repository.list_for_subject(user_id, subject_id)
        if not questions:
            raise ConflictError("There is no quiz to submit yet.", code="no_quiz")

        results: list[QuizQuestionResult] = []
        score = 0
        for q in questions:
            selected = submission.answers.get(q.id)
            correct = selected == q.correct_answer
            score += int(correct)
            results.append(
                QuizQuestionResult(
                    quiz_id=q.id,
                    question=q.question,
                    selected=selected,
                    correct_answer=q.correct_answer,
                    is_correct=correct,
                    explanation=q.explanation,
                    options={"A": q.option_a, "B": q.option_b, "C": q.option_c, "D": q.option_d},
                )
            )

        attempt = self.repository.create_attempt(
            QuizAttempt(
                user_id=user_id,
                subject_id=subject_id,
                score=score,
                total=len(questions),
                answers={str(k): v for k, v in submission.answers.items() if k in {q.id for q in questions}},
            )
        )
        return QuizAttemptResponse(
            id=attempt.id, score=score, total=len(questions),
            accuracy=_accuracy(score, len(questions)), created_at=attempt.created_at, results=results,
        )

    def attempts(self, user_id: UUID, subject_id: UUID) -> list[QuizAttemptSummary]:
        require_subject(self.db, user_id, subject_id)
        return [
            QuizAttemptSummary(
                id=a.id, score=a.score, total=a.total,
                accuracy=_accuracy(a.score, a.total), created_at=a.created_at,
            )
            for a in self.repository.list_attempts(user_id, subject_id)
        ]
