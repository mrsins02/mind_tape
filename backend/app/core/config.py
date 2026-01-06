from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "MindTape"
    debug: bool = Field(
        alias="DEBUG",
        default=False,
    )

    # API Keys
    api_key: str = Field(
        alias="MINDTAPE_API_KEY",
        default="dev-api-key-change-in-production",
    )
    openai_api_key: str = Field(
        alias="OPENAI_API_KEY",
        default=None,
    )
    openai_model: str = Field(
        alias="OPENAI_MODEL",
        default="gpt-3.5-turbo",
    )

    # Database
    database_url: str = Field(
        alias="DATABASE_URL",
        default="sqlite+aiosqlite:///./mindtape.db",
    )

    # Vector / Embeddings
    chroma_persist_dir: str = Field(
        alias="CHROMA_PERSIST_DIR",
        default="./chroma_data",
    )
    embedding_model: str = Field(
        alias="EMBEDDING_MODEL",
        default="all-MiniLM-L6-v2",
    )

    # Chunking
    chunk_size: int = Field(
        alias="CHUNK_SIZE",
        default=500,
    )
    chunk_overlap: int = Field(
        alias="CHUNK_OVERLAP",
        default=50,
    )
    max_results: int = Field(
        alias="MAX_RESULTS",
        default=10,
    )

    # CORS
    cors_origins: list[str] = Field(
        alias="CORS_ORIGINS",
        default=["*"],
    )

    # Logging
    log_level: str = Field(
        alias="LOG_LEVEL",
        default="INFO",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
