"""Heuristic prompt-injection detection.

Document text is *always* treated as data (see the prompts).  Detection is only
used for observability - we log that a retrieved chunk looked like an attack -
we never rely on it as the security boundary.
"""

from __future__ import annotations

import re

_PATTERNS: dict[str, re.Pattern[str]] = {
    "ignore_instructions": re.compile(
        r"\b(ignore|disregard|forget|override)\b.{0,40}\b(previous|prior|above|earlier|all|system)\b.{0,30}\b(instruction|prompt|rule|message)s?\b",
        re.IGNORECASE | re.DOTALL,
    ),
    "reveal_prompt": re.compile(
        r"\b(reveal|show|print|leak|output|repeat)\b.{0,40}\b(system prompt|instructions|hidden prompt|initial prompt)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    "secrets": re.compile(
        r"\b(api[\s_-]?key|secret[\s_-]?key|password|access token|environment variable|credentials?)\b.{0,40}\b(reveal|show|print|send|leak|give|tell)\b"
        r"|\b(reveal|show|print|send|leak|give|tell)\b.{0,40}\b(api[\s_-]?key|secret[\s_-]?key|password|access token|environment variables?|credentials?)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    "role_override": re.compile(
        r"\b(you are now|act as|pretend to be|from now on you)\b", re.IGNORECASE
    ),
    "fake_delimiter": re.compile(r"<\s*/?\s*(system|assistant|retrieved_context)\b", re.IGNORECASE),
}


def scan_for_injection(text: str) -> list[str]:
    """Return the names of suspicious patterns found in ``text``."""
    if not text:
        return []
    return [name for name, pattern in _PATTERNS.items() if pattern.search(text)]
