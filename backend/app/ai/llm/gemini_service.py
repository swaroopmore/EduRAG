"""Gemini access (via LangChain) with defensive error handling."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Iterator

from app.core.config import settings
from app.core.errors import AIServiceError, AINotConfiguredError
from app.core.logging import get_logger

logger = get_logger("llm")


def _content_to_text(content: Any) -> str:
    """Gemini may return a string or a list of content parts."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and part.get("type", "text") == "text":
                parts.append(str(part.get("text", "")))
        return "".join(parts)
    return str(content)


def _translate_error(exc: Exception) -> AIServiceError | AINotConfiguredError:
    message = str(exc).lower()
    if "api key" in message or "api_key" in message or "permission_denied" in message:
        logger.error("Gemini rejected the API key: %s", type(exc).__name__)
        return AINotConfiguredError()
    if "429" in message or "quota" in message or "resource_exhausted" in message or "rate" in message:
        return AIServiceError(
            "The AI service is busy right now. Please try again in a minute.",
            code="ai_busy",
        )
    if "timeout" in message or "deadline" in message:
        return AIServiceError(
            "The AI took too long to respond. Please try again.", code="ai_timeout"
        )
    return AIServiceError()


class GeminiService:
    def __init__(self) -> None:
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not settings.GEMINI_API_KEY:
                raise AINotConfiguredError()
            from langchain_google_genai import ChatGoogleGenerativeAI

            self._client = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=settings.GEMINI_TEMPERATURE,
                timeout=settings.GEMINI_TIMEOUT_SECONDS,
                max_retries=settings.GEMINI_MAX_RETRIES,
            )
        return self._client

    @staticmethod
    def _messages(system: str | None, user: str) -> list[tuple[str, str]]:
        messages: list[tuple[str, str]] = []
        if system:
            messages.append(("system", system))
        messages.append(("human", user))
        return messages

    def generate(self, user: str, system: str | None = None) -> str:
        try:
            response = self.client.invoke(self._messages(system, user))
        except (AIServiceError, AINotConfiguredError):
            raise
        except Exception as exc:  # noqa: BLE001
            logger.error("Gemini call failed: %s: %s", type(exc).__name__, exc)
            raise _translate_error(exc) from exc
        return _content_to_text(getattr(response, "content", response)).strip()

    def stream(self, user: str, system: str | None = None) -> Iterator[str]:
        try:
            for chunk in self.client.stream(self._messages(system, user)):
                text = _content_to_text(getattr(chunk, "content", ""))
                if text:
                    yield text
        except (AIServiceError, AINotConfiguredError):
            raise
        except Exception as exc:  # noqa: BLE001
            logger.error("Gemini stream failed: %s: %s", type(exc).__name__, exc)
            raise _translate_error(exc) from exc


@lru_cache(maxsize=1)
def get_llm() -> GeminiService:
    return GeminiService()
