from pydantic import BaseModel


class Citation(BaseModel):
    document: str
    page: int
    snippet: str