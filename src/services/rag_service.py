from openai import OpenAI
from src.config import get_settings
from src.models import Citation, RAGResult
from src.services.embedding_service import EmbeddingService
from src.services.extraction_service import ExtractionService
from src.services.milvus_repository import MilvusRepository


class RAGService:
    def __init__(self):
        settings = get_settings()
        self.settings = settings
        self.extractor = ExtractionService()
        self.embedding_service = EmbeddingService()
        self.milvus_repository = MilvusRepository()
        self.client = OpenAI(api_key=settings.azure_openai_api_key, base_url=settings.azure_base_url)

    def solve(self, error_text: str, user_note: str = "") -> RAGResult:
        extracted = self.extractor.extract(error_text)

        search_query = self.extractor.build_search_query(
            original_text=error_text,
            extracted=extracted,
            user_note=user_note
        )

        query_vector = self.embedding_service.embed([search_query])[0]

        hits = self.milvus_repository.search(
            vector=query_vector,
            top_k=self.settings.top_k
        )

        relevant_hits = [
            hit for hit in hits
            if hit.score >= self.settings.min_retrieval_score
        ]

        if not relevant_hits:
            return RAGResult(
                answer="The input is a technical error, but no sufficiently relevant knowledge was found in the knowledge base.",
                extracted=extracted,
                search_query=search_query,
                knowledge=[],
                citations=[]
            )

        context_parts = []
        citations = []

        for index, hit in enumerate(relevant_hits, start=1):
            source_id = f"Source {index}"

            context_parts.append(
                f"[{source_id}]\n"
                f"Title: {hit.title}\n"
                f"Source URL: {hit.source_url}\n"
                f"Chunk: {hit.chunk_index}\n\n"
                f"{hit.text}"
            )

            citations.append(
                Citation(
                    source_id=source_id,
                    title=hit.title,
                    source_url=hit.source_url,
                    path=hit.path,
                    chunk_index=hit.chunk_index,
                    score=hit.score,
                    snippet=hit.text[:500]
                )
            )

        context = "\n\n".join(context_parts)

        prompt = f"""
You are a technical support assistant.

Only answer software and system error questions.

Use only the retrieved knowledge below.

Do not invent causes, commands, configurations, or solutions.

Return:
1. Error
2. Possible cause
3. Solution
4. Verification steps

Use citations like [Source 1], [Source 2].

ERROR:
{error_text}

USER NOTE:
{user_note or "(none)"}

EXTRACTED INFORMATION:
{extracted.model_dump_json(indent=2)}

RETRIEVED KNOWLEDGE:
{context}
"""

        response = self.client.responses.create(
            model=self.settings.azure_openai_generation_deployment,
            input=prompt
        )

        return RAGResult(
            answer=response.output_text.strip(),
            extracted=extracted,
            search_query=search_query,
            knowledge=relevant_hits,
            citations=citations
        )