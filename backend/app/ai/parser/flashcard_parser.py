from app.ai.parser.base import StructuredParser
from app.ai.parser.schemas import FlashcardItem


class FlashcardParser(StructuredParser):
    item_model = FlashcardItem
    wrapper_keys = ("flashcards", "cards")
    min_items = 3
    max_items = 30
    label = "flashcards"

    @classmethod
    def _post(cls, items):
        seen, unique = set(), []
        for item in items:
            key = item.question.lower()
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique
