from hashlib import sha256

from pymilvus import MilvusClient

from src.config import get_settings
from src.models import KnowledgeHit


class MilvusRepository:
    def __init__(self):
        settings = get_settings()

        self.collection_name = (
            settings.milvus_collection
        )

        self.client = MilvusClient(
            uri=settings.milvus_lite_path
        )

    def exists(self) -> bool:
        return self.client.has_collection(
            collection_name=self.collection_name
        )

    def reset(self) -> None:
        if self.exists():
            self.client.drop_collection(
                collection_name=self.collection_name
            )

    def create_collection(
        self,
        dimension: int,
    ) -> None:
        if self.exists():
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            dimension=dimension,
            metric_type="COSINE",
            auto_id=False,
        )

    @staticmethod
    def create_id(
        source_url: str,
        chunk_index: int,
    ) -> int:
        raw = (
            f"{source_url}"
            f"#{chunk_index}"
        )

        digest = sha256(
            raw.encode("utf-8")
        ).digest()[:8]

        return (
            int.from_bytes(
                digest,
                "big",
            )
            & ((1 << 63) - 1)
        )

    def insert(self, chunks: list[dict],vectors: list[list[float]]) -> int:
        if not chunks:
            return 0

        if len(chunks) != len(vectors):
            raise ValueError("Chunks and vectors length mismatch.")

        self.create_collection(
            dimension=len(vectors[0])
        )

        rows = []

        for chunk, vector in zip(
            chunks,
            vectors,
        ):
            rows.append(
              {
                    "id": self.create_id(
                        chunk["source_url"],
                        chunk["chunk_index"],
                    ),
                    "vector": vector,
                    "text": chunk["text"],
                    "title": chunk.get("title", ""),
                    "source_url": chunk.get("source_url", ""),
                    "category": chunk.get("category", ""),
                    "chunk_index": chunk.get("chunk_index", 0),
                }
            )

        self.client.upsert(
            collection_name=self.collection_name,
            data=rows,
        )

        return len(rows)

    def search(
        self, vector: list[float],top_k: int = 5) -> list[KnowledgeHit]:
        if not self.exists():
            return []

        self.client.load_collection(collection_name=self.collection_name)
        
        results = self.client.search(
          collection_name=self.collection_name,
            data=[vector],
            limit=top_k,
            output_fields=[
                "text",
                "title",
                "source_url",
                "chunk_index",
            ],
            search_params={
                "metric_type": "COSINE",
                "params": {},
            },
        )

        hits = []

        if not results:
            return hits

        for hit in results[0]:
            entity = hit.get(
                "entity",
                {},
            )

            hits.append(
              KnowledgeHit(
                    score=float(hit.get("distance", 0.0)),
                    title=str(entity.get("title", "")),
                    text=str(entity.get("text", "")),
                    source_url=str(entity.get("source_url", "")),
                    chunk_index=int(entity.get("chunk_index", 0)),
                )
            )

        return hits