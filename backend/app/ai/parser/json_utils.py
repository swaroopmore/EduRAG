"""Robust extraction of JSON from LLM text."""

from __future__ import annotations

import json
import re
from typing import Any

_FENCE = re.compile(r"^```[a-zA-Z0-9_-]*\s*\n?|\n?```\s*$")


class ParseError(ValueError):
    """The model output could not be turned into valid structured data."""


class EmptyResultError(ParseError):
    """The model validly answered "nothing" ([]) - retrying will not help."""


def extract_json(text: str | None) -> Any:
    """Find and decode the first JSON array/object in ``text``.

    Handles markdown fences, leading/trailing commentary and smart quotes around
    the payload.  Raises ``ParseError`` when nothing decodable is found.
    """
    if not text or not text.strip():
        raise ParseError("The model returned an empty response.")

    cleaned = text.strip()
    # Strip a surrounding markdown fence (```json ... ```).
    previous = None
    while previous != cleaned:
        previous = cleaned
        cleaned = _FENCE.sub("", cleaned).strip()

    decoder = json.JSONDecoder()
    for match in re.finditer(r"[\[{]", cleaned):
        try:
            value, _end = decoder.raw_decode(cleaned[match.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(value, (list, dict)):
            return value
    raise ParseError("The model did not return valid JSON.")


def unwrap_list(payload: Any, keys: tuple[str, ...]) -> list:
    """Accept ``[...]`` or ``{"notes": [...]}``-style wrappers."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in keys:
            if isinstance(payload.get(key), list):
                return payload[key]
        lists = [v for v in payload.values() if isinstance(v, list)]
        if len(lists) == 1:
            return lists[0]
    raise ParseError("The model returned JSON in an unexpected shape.")
