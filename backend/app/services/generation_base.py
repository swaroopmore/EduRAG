"""Shared machinery for generating notes / flashcards / quizzes / study plans.

* content is drawn from ALL ready documents of the subject (evenly sampled when it
  exceeds the context budget) instead of a handful of "top-k" chunks
* output is validated with Pydantic before touching the database
* regeneration replaces the old resources in a single transaction
* a per-(user, subject, kind) lock prevents double-clicks from running (and paying
  for) the same generation twice
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Any, ClassVar, Iterator, Type
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.generation import run_structured
from app.ai.parser.base import StructuredParser
from app.ai.rag.context import format_material, select_broad_chunks
from app.ai.vectorstore.chroma_service import get_vectorstore
from app.core.config import settings
from app.core.errors import ConflictError, NoContentError
from app.core.logging import get_logger, short_id, timed
from app.repositories.subject_resource_repository import SubjectResourceRepository
from app.services.access import require_ready_documents, require_subject

logger = get_logger("generation")

_in_flight: set[tuple[str, str, str]] = set()
_in_flight_lock = threading.Lock()


@contextmanager
def generation_lock(user_id: UUID, subject_id: UUID, kind: str) -> Iterator[None]:
    key = (str(user_id), str(subject_id), kind)
    with _in_flight_lock:
        if key in _in_flight:
            raise ConflictError(
                "This is already being generated. Please wait a moment.", code="already_generating"
            )
        _in_flight.add(key)
    try:
        yield
    finally:
        with _in_flight_lock:
            _in_flight.discard(key)


class BaseGenerationService:
    kind: ClassVar[str]
    parser: ClassVar[Type[StructuredParser]]
    repository_cls: ClassVar[Type[SubjectResourceRepository]]

    def __init__(self, db: Session):
        self.db = db
        self.repository = self.repository_cls(db)

    # ------------------------------------------------------------- overridables
    def build_prompts(self, material: str, **params: Any) -> tuple[str, str]:
        raise NotImplementedError

    def to_models(self, items: list, user_id: UUID, subject_id: UUID) -> list:
        raise NotImplementedError

    # ---------------------------------------------------------------- workflow
    def prepare_material(self, user_id: UUID, subject_id: UUID) -> str:
        require_subject(self.db, user_id, subject_id)
        ready_ids = require_ready_documents(self.db, user_id, subject_id)
        chunks = get_vectorstore().get_chunks(user_id, subject_id, ready_ids)
        if not chunks:
            raise NoContentError(
                "We couldn't read any indexed content for this subject. Open the Documents "
                "page and re-index your documents."
            )
        selected = select_broad_chunks(chunks, settings.GENERATION_CONTEXT_CHARS)
        material = format_material(selected, settings.GENERATION_CONTEXT_CHARS)
        logger.info(
            "material user=%s subject=%s kind=%s chunks=%d/%d chars=%d",
            short_id(user_id), short_id(subject_id), self.kind, len(selected), len(chunks), len(material),
        )
        return material

    def generate(self, user_id: UUID, subject_id: UUID, **params: Any) -> dict:
        with generation_lock(user_id, subject_id, self.kind):
            with timed() as t:
                material = self.prepare_material(user_id, subject_id)
                system, user = self.build_prompts(material, **params)
                items = run_structured(
                    operation=self.kind, system=system, user=user, parser=self.parser
                )
                count = self.repository.replace_for_subject(
                    user_id, subject_id, self.to_models(items, user_id, subject_id)
                )
        logger.info(
            "generated kind=%s user=%s subject=%s count=%d ms=%s",
            self.kind, short_id(user_id), short_id(subject_id), count, t["ms"],
        )
        return {"generated": count}

    def list(self, user_id: UUID, subject_id: UUID) -> list:
        require_subject(self.db, user_id, subject_id)
        return self.repository.list_for_subject(user_id, subject_id)
