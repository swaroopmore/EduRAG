from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.repositories.study_plan_repository import (
    StudyPlanRepository,
)
from app.schemas.study_plan import (
    GenerateStudyPlanResponse,
    StudyPlanResponse,
)
from app.services.study_plan_service import (
    StudyPlanService,
)

router = APIRouter(
    prefix="/study-plans",
    tags=["Study Planner"],
)


@router.post(
    "/generate/{subject_id}",
    response_model=GenerateStudyPlanResponse,
)
def generate_study_plan(
    subject_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = StudyPlanService(
        StudyPlanRepository(db)
    )

    return service.generate(
        user_id=current_user.id,
        subject_id=subject_id,
    )


@router.get(
    "/{subject_id}",
    response_model=list[StudyPlanResponse],
)
def get_study_plan(
    subject_id: UUID,
    db: Session = Depends(get_db),
):

    service = StudyPlanService(
        StudyPlanRepository(db)
    )

    return service.get_study_plan(
        subject_id,
    )