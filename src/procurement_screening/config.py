"""Application settings, loaded from environment variables / .env."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3.2"
    embedding_model: str = "nomic-embed-text"
    llm_num_ctx: int = 4096
    llm_cache_dir: str = "data/cache/llm"
    llm_timeout_s: float = 120.0
    qdrant_path: str = "data/qdrant"


def get_settings() -> Settings:
    return Settings()
