from app.ai.parser.base import StructuredParser
from app.ai.parser.schemas import StudyPlanItem


class StudyPlanParser(StructuredParser):
    item_model = StudyPlanItem
    wrapper_keys = ("plan", "study_plan", "days", "schedule")
    min_items = 1
    max_items = 60
    label = "study plan"

    @classmethod
    def _post(cls, items):
        # one session per day, ordered by day
        by_day: dict[int, StudyPlanItem] = {}
        for item in items:
            by_day.setdefault(item.day, item)
        return [by_day[d] for d in sorted(by_day)]
