from pydantic import BaseModel


class KnowledgeHit(BaseModel):
    score: float
    title: str = ""
    text: str = ""
    source_url: str = ""
    repo: str = ""
    path: str = ""
    chunk_index: int = 0