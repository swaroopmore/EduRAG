from uuid import UUID

from pydantic import BaseModel


class Citation(BaseModel):
    document: str | None = None
    document_id: UUID | None = None
    page: int | None = None
    unit: str | None = None  # "page" | "slide"
    snippet: str = ""
    ref: int | None = None  # matches the [n] markers inside the answer
