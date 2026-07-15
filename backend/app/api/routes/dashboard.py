from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db

from app.models.user import User

from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService


router = APIRouter(

    prefix="/dashboard",

    tags=["Dashboard"]

)


@router.get(

    "",

    response_model=DashboardResponse

)

def get_dashboard(

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    repository = DashboardRepository(db)

    service = DashboardService(repository)

    return service.get_dashboard(

        current_user.id

    )