from app.models.study_plan import StudyPlan
from app.repositories.subject_resource_repository import SubjectResourceRepository


class StudyPlanRepository(SubjectResourceRepository[StudyPlan]):
    model = StudyPlan
    order_by = (StudyPlan.day.asc(), StudyPlan.created_at.asc())
