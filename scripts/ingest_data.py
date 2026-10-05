from src.services.loader import DocumentLoader
from src.services.chunking_service import ChunkingService
from src.services.embedding_service import EmbeddingService
from src.services.milvus_repository import MilvusRepository

BATCH_SIZE = 32


def batch_items(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def main():
    loader = DocumentLoader()
    chunker = ChunkingService(chunk_size=450, overlap=80)
    embedder = EmbeddingService()
    milvus = MilvusRepository()

    documents = loader.load_folder("knowledge")

    milvus.reset()

    total_chunks = 0

    for document in documents:
        print(f"\nLoading: {document['metadata']['title']}")

        chunks = chunker.chunk_document(
            text=document["text"],
            metadata=document["metadata"]
        )

        print(f"Chunks: {len(chunks)}")

        for batch in batch_items(chunks, BATCH_SIZE):
            texts = [item["text"] for item in batch]
            vectors = embedder.embed(texts)
            inserted = milvus.insert(batch, vectors)
            total_chunks += inserted
            print(f"Inserted total: {total_chunks}")

    print("\nDONE")
    print(f"Documents: {len(documents)}")
    print(f"Total chunks: {total_chunks}")


if __name__ == "__main__":
    main()