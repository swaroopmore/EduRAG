import re

from app.ai.guardrails.sanitize import clean_text, neutralize_delimiters
from app.ai.llm import gemini_service
from app.ai.query_rewriter.prompt import (
    QUERY_REWRITE_SYSTEM_PROMPT,
    QUERY_REWRITE_USER_PROMPT,
)
from app.core.errors import AIServiceError
from app.core.logging import get_logger

logger = get_logger("rewriter")

_PRONOUNS = re.compile(
    r"\b(it|its|this|that|they|them|their|these|those|he|she|there|the same|above|previous|earlier|more|another|else)\b",
    re.IGNORECASE,
)


def needs_rewrite(question: str, has_history: bool) -> bool:
    """Only spend an LLM call when the question is likely a follow-up."""
    if not has_history:
        return False
    words = question.split()
    return len(words) <= 8 or bool(_PRONOUNS.search(question))


class QueryRewriter:
    def rewrite(self, question: str, history: str) -> str:
        prompt = QUERY_REWRITE_USER_PROMPT.format(
            history=history, question=neutralize_delimiters(question)
        )
        try:
            rewritten = gemini_service.get_llm().generate(prompt, system=QUERY_REWRITE_SYSTEM_PROMPT)
        except AIServiceError as exc:
            # Rewriting is an optimisation - fall back to the original question.
            logger.warning("query rewrite skipped: %s", exc.message)
            return question

        rewritten = clean_text(rewritten).splitlines()[0].strip() if rewritten else ""
        rewritten = rewritten.strip("\"' ")
        if not rewritten or len(rewritten) > 400:
            return question
        return rewritten
