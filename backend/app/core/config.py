"""
LEDGER — Application Configuration
Loads all settings from environment variables via pydantic-settings.
No secrets are hardcoded here.
"""
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: Literal["development", "production", "test"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    app_name: str = "LEDGER Credit Intelligence"
    app_version: str = "1.0.0"

    # JWT / Security  (env var: SECRET_KEY or JWT_SECRET_KEY)
    secret_key: str = Field(default="ledger-dev-secret-change-in-production-32chars-min", min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    @property
    def jwt_secret_key(self) -> str:
        return self.secret_key

    @property
    def jwt_algorithm(self) -> str:
        return self.algorithm

    @property
    def jwt_access_token_expire_minutes(self) -> int:
        return self.access_token_expire_minutes

    # Database (absolute path to project root ledger.db)
    database_url: str = f"sqlite+aiosqlite:///{(Path(__file__).resolve().parent.parent.parent.parent / 'ledger.db').as_posix()}"
    database_url_sync: str = "postgresql+psycopg2://ledger:ledger_pass@localhost:5432/ledger_db"
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # pgvector
    vector_dimensions: int = 384

    # LLM
    llm_provider: Literal["ollama", "mock", "future_cloud"] = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    ollama_timeout_seconds: int = 60

    # Demo / Mock
    demo_mode: bool = False
    demo_cache_dir: str = "data/demo_cache"

    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_batch_size: int = 32

    # ML
    model_path: str = "ml/models/xgb_credit_model.pkl"
    calibrator_path: str = "ml/models/isotonic_calibrator.pkl"
    feature_version: str = "v1.0"
    model_version: str = "xgb-v1.0"

    # File uploads
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 10
    allowed_mime_types: list[str] = ["application/pdf", "image/png", "image/jpeg"]

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Rate limiting
    rate_limit_copilot: str = "10/minute"
    rate_limit_events: str = "20/minute"

    # Quantum
    enable_quantum: bool = False

    # Demo credentials (seeded — for demo only)
    demo_underwriter_email: str = "sarah.chen@ledger.demo"
    demo_underwriter_password: str = "LedgerDemo2026!"
    demo_admin_email: str = "admin@ledger.demo"
    demo_admin_password: str = "LedgerAdmin2026!"

    @computed_field
    @property
    def is_demo_mode(self) -> bool:
        return self.demo_mode or self.llm_provider == "mock"

    @computed_field
    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — loaded once at startup."""
    return Settings()


settings = get_settings()
