"""Centralised application configuration.

Every infrastructure-specific value (paths, model names, URLs, limits) is read
from environment variables so the same code runs in development, Docker and
Railway without edits.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ------------------------------------------------------------------ app
    PROJECT_NAME: str = "EduRAG"
    PROJECT_VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"  # development | production | test
    LOG_LEVEL: str = "INFO"

    # ------------------------------------------------------------- database
    DATABASE_URL: str
    DB_ECHO: bool = False
    RUN_MIGRATIONS_ON_START: bool = True  # used by scripts/start.sh

    # ----------------------------------------------------------------- auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ------------------------------------------------------------------ CORS
    # Comma separated list of allowed browser origins, e.g.
    # "https://edurag.vercel.app,http://localhost:5173".  "*" keeps the old
    # behaviour (safe here because auth uses bearer tokens, not cookies).
    CORS_ORIGINS: str = "*"

    # ------------------------------------------------------------------- LLM
    # GOOGLE_API_KEY is accepted as an alias because .env.example used it.
    GEMINI_API_KEY: str = Field(
        default="",
        validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    )
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_TEMPERATURE: float = 0.2
    GEMINI_TIMEOUT_SECONDS: int = 90
    GEMINI_MAX_RETRIES: int = 2

    # ------------------------------------------------------- vector storage
    VECTOR_DB_PATH: str = "vector_db"
    CHROMA_COLLECTION: str = "edurag"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    RERANKER_ENABLED: bool = True
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    PRELOAD_MODELS: bool = True

    # ------------------------------------------------------------- ingestion
    UPLOAD_DIR: str = "uploads/documents"
    MAX_UPLOAD_MB: int = 25
    ALLOWED_FILE_TYPES: str = "pdf,txt,docx,pptx"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MIN_CHUNK_CHARS: int = 40
    INGESTION_WORKERS: int = 2
    RUN_STARTUP_RECOVERY: bool = True

    # ------------------------------------------------------------- retrieval
    RETRIEVAL_TOP_K: int = 6
    RETRIEVAL_CANDIDATES: int = 20
    MAX_CONTEXT_CHARS: int = 12000
    GENERATION_CONTEXT_CHARS: int = 24000
    # Cross-encoder logit below which a chunk is considered irrelevant.
    RERANK_MIN_SCORE: float = -8.0
    # Cosine similarity below which a vector hit alone is not trusted.
    MIN_VECTOR_SIMILARITY: float = 0.2

    # ---------------------------------------------------------------- limits
    MAX_QUESTION_CHARS: int = 2000
    MAX_ANSWER_CHARS: int = 8000
    CHAT_RATE_LIMIT_PER_MINUTE: int = 20
    GENERATION_RATE_LIMIT_PER_MINUTE: int = 6
    LOGIN_RATE_LIMIT_PER_5_MIN: int = 10
    REGISTER_RATE_LIMIT_PER_HOUR: int = 20

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    # ------------------------------------------------------------ validators
    @field_validator("DATABASE_URL")
    @classmethod
    def _normalise_database_url(cls, value: str) -> str:
        # Railway/Heroku style URLs use the legacy "postgres://" scheme which
        # SQLAlchemy 2 no longer accepts.
        if value.startswith("postgres://"):
            return "postgresql://" + value[len("postgres://"):]
        return value

    # ------------------------------------------------------------ properties
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def cors_origins_list(self) -> list[str]:
        origins = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        return origins or ["*"]

    @property
    def allowed_file_types(self) -> set[str]:
        return {t.strip().lower().lstrip(".") for t in self.ALLOWED_FILE_TYPES.split(",") if t.strip()}

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
