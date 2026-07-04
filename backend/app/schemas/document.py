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
    created_at: datetime