from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    subject_id: UUID
    subject_name: str | None = None
    status: str
    stage: str | None = None
    error_message: str | None = None
    page_count: int | None = None
    chunk_count: int | None = None
    created_at: datetime
    processed_at: datetime | None = None
