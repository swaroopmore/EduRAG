"""Post-generation guardrails for free-text answers."""

from __future__ import annotations

import re

from app.ai.guardrails.sanitize import clean_text, truncate
from app.core.config import settings

_SECRET_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z_\-]{30,}"),                       # Google API keys
    re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}"),                      # generic secret keys
    re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"),  # JWTs
    re.compile(r"postgres(?:ql)?://[^\s'\"]+"),                   # DB URLs
]


def _configured_secrets() -> list[str]:
    values = [settings.SECRET_KEY, settings.GEMINI_API_KEY]
    return [v for v in values if v and len(v) >= 8]


def redact_secrets(text: str) -> str:
    for secret in _configured_secrets():
        text = text.replace(secret, "[redacted]")
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[redacted]", text)
    return text


def scrub_answer(text: str | None) -> str:
    """Clean, redact and bound an LLM answer before it is stored or shown."""
    text = clean_text(text)
    text = redact_secrets(text)
    return truncate(text, settings.MAX_ANSWER_CHARS)
