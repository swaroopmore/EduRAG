from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.flashcard import Flashcard
from app.models.note import Note
from app.models.quiz import Quiz
from app.models.study_plan import StudyPlan
from app.models.subject import Subject


class DashboardRepository:

    def __init__(
        self,
        db: Session,
    ):

        self.db = db

    def count_subjects(
        self,
        user_id: UUID,
    ):

        return (

            self.db.query(
                Subject
            )

            .filter(

                Subject.user_id
                == user_id

            )

            .count()

        )

    def count_documents(
    self,
    user_id: UUID,
):

       return (

        self.db.query(
            Document
        )

        .join(
            Subject
        )

        .filter(

            Subject.user_id == user_id

        )

        .count()

    )
    def count_flashcards(
        self,
        user_id: UUID,
    ):

        return (

            self.db.query(
                Flashcard
            )

            .filter(

                Flashcard.user_id
                == user_id

            )

            .count()

        )

    def count_quizzes(
        self,
        user_id: UUID,
    ):

        return (

            self.db.query(
                Quiz
            )

            .filter(

                Quiz.user_id
                == user_id

            )

            .count()

        )

    def count_notes(
        self,
        user_id: UUID,
    ):

        return (

            self.db.query(
                Note
            )

            .filter(

                Note.user_id
                == user_id

            )

            .count()

        )

    def count_study_plans(
        self,
        user_id: UUID,
    ):

        return (

            self.db.query(
                StudyPlan
            )

            .filter(

                StudyPlan.user_id
                == user_id

            )

            .count()

        )

    def storage_used(
        self,
        user_id: UUID,
    ):

        total = (

            self.db.query(

                func.sum(
                    Document.file_size
                )

            )

            .filter(

                Subject.user_id
                == user_id

            )

            .scalar()

        )

        if total is None:

            return 0.0

        return round(

            total / (1024 * 1024),

            2,

        )