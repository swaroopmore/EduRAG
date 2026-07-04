from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.repositories.subject_repository import SubjectRepository
from app.schemas.subject import SubjectCreate, SubjectResponse
from app.services.subject_service import SubjectService

router = APIRouter(
    prefix="/subjects",
    tags=["Subjects"],
)


@router.post("", response_model=SubjectResponse)
def create_subject(
    subject: SubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    service = SubjectService(
        SubjectRepository(db)
    )

    return service.create(
        subject.name,
        subject.description,
        current_user.id,
    )


@router.get("", response_model=list[SubjectResponse])
def get_subjects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    service = SubjectService(
        SubjectRepository(db)
    )

    return service.get_all(current_user.id)