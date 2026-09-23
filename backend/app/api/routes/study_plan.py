from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.core.rate_limit import user_rate_limit
from app.database.session import get_db
from app.models.user import User
from app.schemas.study_plan import GenerateStudyPlanResponse, StudyPlanResponse, StudyPlanUpdate
from app.services.study_plan_service import StudyPlanService

router = APIRouter(prefix="/study-plans", tags=["Study Planner"])

_limit = user_rate_limit("generate", lambda: settings.GENERATION_RATE_LIMIT_PER_MINUTE)


@router.post("/generate/{subject_id}", response_model=GenerateStudyPlanResponse, dependencies=[Depends(_limit)])
def generate_study_plan(
    subject_id: UUID,
    days: int = Query(7, ge=3, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StudyPlanService(db).generate(current_user.id, subject_id, days=days)


@router.get("/{subject_id}", response_model=list[StudyPlanResponse])
def get_study_plan(
    subject_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StudyPlanService(db).get_study_plan(current_user.id, subject_id)


@router.patch("/item/{plan_id}", response_model=StudyPlanResponse)
def update_study_session(
    plan_id: UUID,
    payload: StudyPlanUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a study session as completed / not completed."""
    return StudyPlanService(db).set_completed(current_user.id, plan_id, payload.completed)
