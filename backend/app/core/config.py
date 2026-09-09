from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Vector store ---
    vector_store_dir: Path = Path("./data/vector_store")
    default_project_id: str = "library_management_demo"

    # --- Project registry (metadata: id, name, created_at, document_count) ---
    project_registry_path: Path = Path("./data/projects.json")

    # --- Embedding model ---
    embedding_model_name: str = "all-MiniLM-L6-v2"

    # --- Retrieval ---
    top_k: int = 4
    distance_threshold: float = 0.75

    # --- Chunking  ---
    chunk_size_words: int = 400
    chunk_overlap_words: int = 60

    # --- Generation ---
    ollama_model: str = "llama3.2"
    ollama_host: str = "http://localhost:11434"

    # --- App ---
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:8501"

    def collection_name(self, project_id: str | None) -> str:
        resolved = project_id or self.default_project_id
        return f"project_{resolved}"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()