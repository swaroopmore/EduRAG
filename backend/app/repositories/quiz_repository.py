from uuid import UUID

from sqlalchemy.orm import Session

from app.models.quiz import Quiz


class QuizRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def create(
        self,
        quiz: Quiz,
    ):

        self.db.add(quiz)

        self.db.commit()

        self.db.refresh(quiz)

        return quiz

    def create_many(
        self,
        quizzes: list[Quiz],
    ):

        self.db.add_all(quizzes)

        self.db.commit()

        return quizzes

    def get_by_subject(
        self,
        subject_id: UUID,
    ):

        return (
            self.db.query(Quiz)
            .filter(
                Quiz.subject_id == subject_id
            )
            .order_by(
                Quiz.created_at.desc()
            )
            .all()
        )

    def delete_by_subject(
        self,
        subject_id: UUID,
    ):

        (
            self.db.query(Quiz)
            .filter(
                Quiz.subject_id == subject_id
            )
            .delete()
        )

        self.db.commit()

    def delete(
        self,
        quiz_id: UUID,
    ):

        quiz = (
            self.db.query(Quiz)
            .filter(
                Quiz.id == quiz_id
            )
            .first()
        )

        if quiz:

            self.db.delete(quiz)

            self.db.commit()

        return quiz