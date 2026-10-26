"""Text sanitisation for anything that flows into an LLM prompt or the database."""

from __future__ import annotations

import re

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_DELIMITERS = re.compile(
    r"<\s*(/?)\s*(retrieved_context|conversation_history|source|untrusted_document)",
    re.IGNORECASE,
)


def clean_text(text: str | None) -> str:
    """Remove NUL/control characters (PostgreSQL rejects NUL) and normalise newlines."""
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return _CONTROL_CHARS.sub("", text).strip()


def neutralize_delimiters(text: str) -> str:
    """Stop document text from closing/opening our prompt delimiters."""
    return _DELIMITERS.sub(lambda m: f"&lt;{m.group(1)}{m.group(2)}", text)


def truncate(text: str, limit: int, suffix: str = "…") -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - len(suffix))].rstrip() + suffix
