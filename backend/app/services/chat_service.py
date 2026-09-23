"""Grounded document Q&A.

Flow: validate ownership -> (optional) follow-up rewrite -> cache -> retrieval
(hybrid, or a broad sample for "summarize"-style requests) -> guarded prompt ->
Gemini -> scrub -> citations -> persist.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Iterator
from uuid import UUID

from langchain_core.documents import Document
from sqlalchemy.orm import Session

from app.ai.guardrails import scrub_answer
from app.ai.llm import gemini_service
from app.ai.memory.formatter import ConversationFormatter
from app.ai.memory.memory_service import MemoryService
from app.ai.prompts.teacher_prompt import BROAD_SCOPE_NOTE, TEACHER_SYSTEM_PROMPT, TEACHER_USER_PROMPT
from app.ai.query_rewriter.query_rewriter import QueryRewriter, needs_rewrite
from app.ai.rag.context import (
    NOT_FOUND_MESSAGE,
    build_citations,
    format_context,
    is_broad_request,
    referenced_sources,
    select_broad_chunks,
)
from app.ai.retrieval.retriever import get_retriever
from app.ai.vectorstore.chroma_service import get_vectorstore
from app.core.config import settings
from app.core.errors import AIServiceError, AppError
from app.core.logging import get_logger, short_id, timed
from app.models.chat_history import ChatHistory
from app.repositories.chat_repository import ChatRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.access import require_ready_documents, require_subject
from app.utils.text import normalize_question

logger = get_logger("chat")

INDEX_EMPTY_MESSAGE = (
    "Your documents don't seem to be searchable right now. Open the Documents page and "
    "re-index them, or upload them again."
)
UNRELATED_MESSAGE = (
    f"{NOT_FOUND_MESSAGE} Try rephrasing your question, or upload material that covers this topic."
)


def is_not_found(answer: str) -> bool:
    return NOT_FOUND_MESSAGE.lower()[:38] in (answer or "").lower()[:160]


@dataclass
class Prepared:
    question: str
    normalized: str
    user_id: UUID
    subject_id: UUID
    user_prompt: str | None = None
    used: list[Document] = field(default_factory=list)
    final: ChatResponse | None = None  # set when no LLM call is needed


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = ChatRepository(db)
        self.documents = DocumentRepository(db)
        self.memory = MemoryService(db)
        self.rewriter = QueryRewriter()

    # ------------------------------------------------------------------ prepare
    def _prepare(self, user_id: UUID, request: ChatRequest) -> Prepared:
        subject_id = request.subject_id
        require_subject(self.db, user_id, subject_id)
        document_ids = require_ready_documents(self.db, user_id, subject_id, request.document_id)
        scope = [request.document_id] if request.document_id else None

        history = self.memory.get_recent_history(user_id, subject_id, limit=5)
        history_text = ConversationFormatter.format(history)

        question = request.question
        search_question = question
        if needs_rewrite(question, bool(history)):
            search_question = self.rewriter.rewrite(question, history_text)

        normalized = normalize_question(search_question)
        if request.document_id:
            normalized += f"|doc:{request.document_id}"

        prepared = Prepared(question=question, normalized=normalized, user_id=user_id, subject_id=subject_id)

        # ---- exact-match cache (never older than the last document change)
        if not request.regenerate:
            cached = self.repository.get_cached_answer(
                user_id, subject_id, normalized, newer_than=self.documents.last_change(subject_id, user_id)
            )
            if cached:
                logger.info("chat cache hit user=%s subject=%s", short_id(user_id), short_id(subject_id))
                prepared.final = ChatResponse(
                    id=cached.id,
                    answer=cached.answer,
                    citations=cached.citations or [],
                    grounded=not is_not_found(cached.answer),
                    cached=True,
                )
                return prepared

        # ---- retrieval
        vectorstore = get_vectorstore()
        broad = is_broad_request(search_question)
        if broad:
            chunks = vectorstore.get_chunks(user_id, subject_id, scope or document_ids)
            docs = select_broad_chunks(chunks, settings.MAX_CONTEXT_CHARS)
            method, empty = "broad", not chunks
        else:
            result = get_retriever().search(search_question, user_id, subject_id, document_ids=scope)
            docs, method, empty = result.documents, result.method, result.empty_index
        logger.info(
            "chat retrieval user=%s subject=%s method=%s chunks=%d", short_id(user_id), short_id(subject_id), method, len(docs)
        )

        if empty:
            prepared.final = ChatResponse(answer=INDEX_EMPTY_MESSAGE, citations=[], grounded=False)
            return prepared
        if not docs:
            prepared.final = self._persist(prepared, UNRELATED_MESSAGE, [], regenerate=request.regenerate)
            return prepared

        formatted = format_context(docs, settings.MAX_CONTEXT_CHARS)
        prepared.used = formatted.used
        prepared.user_prompt = TEACHER_USER_PROMPT.format(
            history=history_text,
            context=formatted.text,
            scope_note=BROAD_SCOPE_NOTE if broad else "",
            question=question,
        )
        return prepared

    # ------------------------------------------------------------------ finish
    def _persist(self, prepared: Prepared, answer: str, citations: list[dict], regenerate: bool = False) -> ChatResponse:
        row = self.repository.replace_same_question(
            ChatHistory(
                user_id=prepared.user_id,
                subject_id=prepared.subject_id,
                question=scrub_answer(prepared.question),
                normalized_question=prepared.normalized,
                answer=answer,
                citations=citations,
            )
        )
        return ChatResponse(
            id=row.id, answer=answer, citations=citations, grounded=not is_not_found(answer)
        )

    def _finish(self, prepared: Prepared, raw_answer: str, regenerate: bool = False) -> ChatResponse:
        answer = scrub_answer(raw_answer)
        if not answer:
            raise AIServiceError("The AI returned an empty answer. Please try again.", code="ai_empty")

        if is_not_found(answer):
            answer = re.sub(r"\s*\[\d{1,2}\]", "", answer).strip()
            citations: list[dict] = []
        else:
            refs = referenced_sources(answer, len(prepared.used))
            # Show only sources the model actually cited; if it cited none, fall back to the top 3.
            citations = build_citations(prepared.used, refs or set(range(1, min(3, len(prepared.used)) + 1)))
        return self._persist(prepared, answer, citations, regenerate)

    # ------------------------------------------------------------------ public
    def ask(self, user_id: UUID, request: ChatRequest) -> ChatResponse:
        with timed() as t:
            prepared = self._prepare(user_id, request)
            if prepared.final is not None:
                return prepared.final
            raw = gemini_service.get_llm().generate(prepared.user_prompt, system=TEACHER_SYSTEM_PROMPT)
            response = self._finish(prepared, raw, request.regenerate)
        logger.info(
            "chat answered user=%s subject=%s sources=%d grounded=%s ms=%s",
            short_id(user_id), short_id(request.subject_id), len(response.citations), response.grounded, t["ms"],
        )
        return response

    def stream(self, user_id: UUID, request: ChatRequest) -> Iterator[str]:
        """Server-sent events: ``token`` chunks, then ``done`` (final answer + citations)."""

        def event(name: str, payload: dict) -> str:
            return f"event: {name}\ndata: {json.dumps(payload, default=str)}\n\n"

        try:
            prepared = self._prepare(user_id, request)
            if prepared.final is not None:
                yield event("done", json.loads(prepared.final.model_dump_json()))
                return

            yield event("start", {"sources": len(prepared.used)})
            parts: list[str] = []
            for token in gemini_service.get_llm().stream(prepared.user_prompt, system=TEACHER_SYSTEM_PROMPT):
                parts.append(token)
                yield event("token", {"t": token})

            response = self._finish(prepared, "".join(parts), request.regenerate)
            yield event("done", json.loads(response.model_dump_json()))
        except AppError as exc:
            yield event("error", {"detail": exc.message, "code": exc.code})
        except Exception:  # noqa: BLE001
            logger.exception("chat stream failed user=%s", short_id(user_id))
            yield event("error", {"detail": "Something went wrong while answering. Please try again.", "code": "internal_error"})

    def history(self, user_id: UUID, subject_id: UUID, limit: int = 50) -> list[ChatHistory]:
        require_subject(self.db, user_id, subject_id)
        return self.repository.list_history(user_id, subject_id, limit)

    def clear_history(self, user_id: UUID, subject_id: UUID) -> int:
        require_subject(self.db, user_id, subject_id)
        return self.repository.clear(user_id, subject_id)
