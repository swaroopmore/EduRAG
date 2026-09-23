from __future__ import annotations

from typing import ClassVar, Generic, TypeVar

from pydantic import BaseModel, ValidationError

from app.ai.parser.json_utils import EmptyResultError, ParseError, extract_json, unwrap_list

T = TypeVar("T", bound=BaseModel)


class StructuredParser(Generic[T]):
    """Validate LLM JSON against a Pydantic model, item by item.

    Invalid items are dropped; if fewer than ``min_items`` survive the whole
    response is rejected with ``ParseError`` (which triggers a retry upstream).
    """

    item_model: ClassVar[type[BaseModel]]
    wrapper_keys: ClassVar[tuple[str, ...]] = ()
    min_items: ClassVar[int] = 1
    max_items: ClassVar[int] = 50
    label: ClassVar[str] = "items"

    @classmethod
    def parse(cls, text: str | None) -> list:
        payload = extract_json(text)
        raw_items = unwrap_list(payload, cls.wrapper_keys)

        valid, problems = [], []
        for raw in raw_items[: cls.max_items * 2]:
            try:
                valid.append(cls.item_model.model_validate(raw))
            except ValidationError as exc:
                problems.append(exc.errors()[0]["msg"] if exc.errors() else "invalid")

        valid = cls._post(valid)[: cls.max_items]
        if len(valid) < cls.min_items:
            if not raw_items:
                raise EmptyResultError(f"The model returned no {cls.label}.")
            raise ParseError(
                f"Only {len(valid)} valid {cls.label} in the response "
                f"({len(problems)} rejected: {'; '.join(sorted(set(problems))[:3])})."
            )
        return valid

    @classmethod
    def _post(cls, items: list) -> list:
        return items
