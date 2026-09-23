from app.ai.parser.base import StructuredParser
from app.ai.parser.schemas import QuizItem


class QuizParser(StructuredParser):
    item_model = QuizItem
    wrapper_keys = ("quiz", "questions", "mcqs")
    min_items = 3
    max_items = 20
    label = "quiz questions"

    @classmethod
    def _post(cls, items):
        seen, unique = set(), []
        for item in items:
            key = item.question.lower()
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique
