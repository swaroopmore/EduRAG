from app.ai.parser.base import StructuredParser
from app.ai.parser.schemas import NoteSection


class NoteParser(StructuredParser):
    item_model = NoteSection
    wrapper_keys = ("notes", "sections", "topics")
    min_items = 1
    max_items = 30
    label = "notes"
