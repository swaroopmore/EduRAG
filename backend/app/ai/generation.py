"""Run an LLM prompt and validate the structured result (with one repair retry)."""

from __future__ import annotations

from typing import Type

from app.ai.llm import gemini_service
from app.ai.parser.base import StructuredParser
from app.ai.parser.json_utils import EmptyResultError, ParseError
from app.core.errors import AIServiceError, NoContentError
from app.core.logging import get_logger, timed

logger = get_logger("generation")

_REPAIR_SUFFIX = (
    "\n\nYour previous reply could not be used: {problem}\n"
    "Reply again with ONLY the JSON array described above - no markdown fences, no commentary."
)


def run_structured(
    *,
    operation: str,
    system: str,
    user: str,
    parser: Type[StructuredParser],
    max_attempts: int = 2,
) -> list:
    """Call the LLM and return validated items, retrying once on malformed output."""
    problem = ""
    for attempt in range(1, max_attempts + 1):
        prompt = user if attempt == 1 else user + _REPAIR_SUFFIX.format(problem=problem)
        with timed() as t:
            text = gemini_service.get_llm().generate(prompt, system=system)
        try:
            items = parser.parse(text)
            logger.info(
                "generation op=%s attempt=%d ok items=%d ms=%s", operation, attempt, len(items), t["ms"]
            )
            return items
        except EmptyResultError:
            logger.info("generation op=%s attempt=%d empty result", operation, attempt)
            raise NoContentError(
                "We couldn't find enough study content in your documents to generate this. "
                "Try uploading more material."
            )
        except ParseError as exc:
            problem = str(exc)
            # Never log the raw model output: it can contain document text.
            logger.warning(
                "generation op=%s attempt=%d invalid output (%s) chars=%d",
                operation, attempt, problem, len(text or ""),
            )

    raise AIServiceError(
        "The AI returned an unexpected format. Please try again.", code="ai_invalid_output"
    )
