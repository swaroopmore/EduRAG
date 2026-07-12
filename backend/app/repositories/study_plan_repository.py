from uuid import UUID

from sqlalchemy.orm import Session

from app.models.study_plan import StudyPlan


class StudyPlanRepository:

    def __init__(
        self,
        db: Session,
    ):

        self.db = db

    def create_many(
        self,
        plans: list[StudyPlan],
    ):

        self.db.add_all(
            plans
        )

        self.db.commit()

        return plans

    def get_by_subject(
        self,
        subject_id: UUID,
    ):

        return (

            self.db.query(
                StudyPlan
            )

            .filter(

                StudyPlan.subject_id
                == subject_id

            )

            .order_by(

                StudyPlan.day.asc(),

                StudyPlan.time.asc(),

            )

            .all()

        )

    def delete_by_subject(
        self,
        subject_id: UUID,
    ):

        (

            self.db.query(
                StudyPlan
            )

            .filter(

                StudyPlan.subject_id
                == subject_id

            )

            .delete()

        )

        self.db.commit()

    def delete(
        self,
        study_plan_id: UUID,
    ):

        plan = (

            self.db.query(
                StudyPlan
            )

            .filter(

                StudyPlan.id
                == study_plan_id

            )

            .first()

        )

        if plan:

            self.db.delete(
                plan
            )

            self.db.commit()

        return plan