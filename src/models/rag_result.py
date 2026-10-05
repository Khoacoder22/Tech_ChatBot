from pydantic import BaseModel

from src.models.extracted_info import ExtractedInfo
from src.models.knowledge_hit import KnowledgeHit
from src.models.citation import Citation


class RAGResult(BaseModel):
    answer: str
    extracted: ExtractedInfo
    search_query: str
    knowledge: list[KnowledgeHit]
    citations: list[Citation]