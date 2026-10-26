"""Context construction for grounded generation.

* ``format_context`` numbers the retrieved chunks ``[1]..[n]`` inside a
  ``<retrieved_context>`` block, neutralising any text that tries to imitate our
  prompt delimiters.
* ``select_broad_chunks`` samples chunks evenly across the whole subject for
  features that must cover *all* the material (notes, quizzes, flashcards, plans).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from langchain_core.documents import Document

from app.ai.guardrails.injection import scan_for_injection
from app.ai.guardrails.sanitize import clean_text, neutralize_delimiters, truncate
from app.core.logging import get_logger

logger = get_logger("context")

NOT_FOUND_MESSAGE = "I couldn't find this information in your uploaded documents."

_BROAD_PATTERNS = re.compile(
    r"\b(summar(?:y|ise|ize|ies)|overview|key (?:concepts?|points?|takeaways?|ideas?)|main (?:points?|ideas?|topics?)"
    r"|important (?:topics?|questions?|concepts?)|interview questions?|table of contents|outline|recap|revise|revision"
    r"|create (?:a )?(?:quiz|mcqs?|flashcards?)|generate (?:a )?(?:quiz|mcqs?|flashcards?)|what (?:is|are) (?:this|these) (?:document|documents|material|topic)s?"
    r"|explain (?:this|it|the (?:document|material|topic)) (?:like|simply|to|in)|explain like|like i'?m (?:a )?beginner|whole (?:document|material))\b",
    re.IGNORECASE,
)


def is_broad_request(question: str) -> bool:
    """True for requests about the material as a whole ("summarize", "key concepts"...)."""
    return bool(_BROAD_PATTERNS.search(question or ""))


@dataclass
class FormattedContext:
    text: str
    used: list[Document]  # chunks in the same order as the [n] numbers


def format_context(docs: list[Document], max_chars: int) -> FormattedContext:
    blocks: list[str] = []
    used: list[Document] = []
    total = 0

    for doc in docs:
        content = neutralize_delimiters(clean_text(doc.page_content))
        if not content:
            continue
        if scan_for_injection(content):
            logger.warning(
                "possible prompt injection inside retrieved chunk (document=%s) - treated as data",
                str(doc.metadata.get("document_id", "-"))[:8],
            )
        label = citation_label(doc)
        block = f'<source id="{len(used) + 1}" file="{_attr(label["document"])}"' + (
            f' {label["unit"]}="{label["page"]}"' if label["page"] is not None else ""
        ) + f">\n{content}\n</source>"
        if used and total + len(block) > max_chars:
            break
        if not used and len(block) > max_chars:
            block = truncate(block, max_chars)
        blocks.append(block)
        used.append(doc)
        total += len(block)

    return FormattedContext(text="\n\n".join(blocks), used=used)


def _attr(value: str | None) -> str:
    return (value or "unknown").replace('"', "'").replace("<", "").replace(">", "")[:120]


def citation_label(doc: Document) -> dict:
    meta = doc.metadata or {}
    page = meta.get("page")
    return {
        "document": meta.get("filename") or "Unknown document",
        "document_id": meta.get("document_id"),
        "page": page + 1 if isinstance(page, int) else None,
        "unit": meta.get("unit") if meta.get("unit") in ("page", "slide") else "page",
    }


def build_citations(docs: list[Document], only_refs: set[int] | None = None) -> list[dict]:
    citations = []
    for index, doc in enumerate(docs, start=1):
        if only_refs is not None and index not in only_refs:
            continue
        label = citation_label(doc)
        citations.append(
            {
                "ref": index,
                "document": label["document"],
                "document_id": label["document_id"],
                "page": label["page"],
                "unit": label["unit"] if label["page"] is not None else None,
                "snippet": truncate(" ".join(clean_text(doc.page_content).split()), 250),
            }
        )
    return citations


_REF = re.compile(r"\[(\d{1,2})\]")


def referenced_sources(answer: str, max_ref: int) -> set[int]:
    return {int(n) for n in _REF.findall(answer) if 1 <= int(n) <= max_ref}


def select_broad_chunks(chunks: list[Document], max_chars: int) -> list[Document]:
    """Pick chunks spread evenly over the material, preserving reading order."""
    if not chunks:
        return []
    total = sum(len(c.page_content) for c in chunks)
    if total <= max_chars:
        return chunks
    avg = max(1, total // len(chunks))
    target = max(1, max_chars // avg)
    if target >= len(chunks):
        return chunks
    step = len(chunks) / target
    picked = [chunks[min(len(chunks) - 1, int(i * step))] for i in range(target)]
    # de-duplicate while preserving order
    seen: set[int] = set()
    unique = []
    for chunk in picked:
        if id(chunk) not in seen:
            seen.add(id(chunk))
            unique.append(chunk)
    return unique


def format_material(chunks: list[Document], max_chars: int) -> str:
    """Plain excerpt block used by the generators (notes, quiz, flashcards, plan)."""
    parts: list[str] = []
    total = 0
    for chunk in chunks:
        content = neutralize_delimiters(clean_text(chunk.page_content))
        if not content:
            continue
        if scan_for_injection(content):
            logger.warning(
                "possible prompt injection inside study material (document=%s) - treated as data",
                str(chunk.metadata.get("document_id", "-"))[:8],
            )
        if parts and total + len(content) > max_chars:
            break
        parts.append(content)
        total += len(content)
    return "\n\n---\n\n".join(parts)
