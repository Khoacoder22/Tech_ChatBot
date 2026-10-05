from openai import OpenAI

from src.config import get_settings


class EmbeddingService:
    def __init__(self):
        settings = get_settings()

        self.model = (
            settings.azure_openai_embedding_deployment
        )

        self.client = OpenAI(
            api_key=settings.azure_openai_api_key,
            base_url=settings.azure_base_url,
        )

    def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        if not texts:
            return []

        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
        )

        data = sorted(
            response.data,
            key=lambda item: item.index,
        )

        return [
            item.embedding
            for item in data
        ]