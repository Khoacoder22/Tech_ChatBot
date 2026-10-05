from pydantic import BaseModel


class Citation(BaseModel):
    source_id: str

    title: str
    source_url: str

    path: str
    chunk_index: int

    score: float
    snippet: str