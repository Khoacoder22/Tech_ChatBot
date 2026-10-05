from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Setting open ai
class Settings(BaseSettings):
    azure_openai_api_key: str
    azure_openai_base_url: str
    
    milvus_lite_path: str = "./data/support_kb.db"
    milvus_collection: str = "support_knowledge"
    
    azure_openai_generation_deployment: str = "gpt-6-luna"
    azure_openai_embedding_deployment: str = "text-embedding-3-small"
    
    top_k: int = 5
    min_retrieval_score: float = 0.35
    
    ocr_langs: str = "en"
    ocr_use_gpu: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    @property
    def azure_base_url(self) -> str:
        return self.azure_openai_base_url
    
    @property
    def ocr_languages(self) -> list[str]:
        return [lang.strip() for lang in self.ocr_langs.split(",")]
    
    def ensure_data_folder(self) -> None:
        db_path = Path(self.milvus_lite_path)
        db_path.parent.mkdir( parents=True, exist_ok=True)

@lru_cache
def get_settings() -> Settings:
    settings = Settings()

    settings.ensure_data_folder()

    return settings
    