from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "CubicDocs AI"
    app_version: str = "1.0.0"
    app_env: Literal["development", "testing", "staging", "production"] = "development"
    debug: bool = True

    api_v1_prefix: str = "/api/v1"
    backend_cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    secret_key: str = "development-only-secret-change-before-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    database_url: str = "sqlite:///./cubicdocs.db"
    redis_url: str = "redis://localhost:6379/0"

    document_storage_path: Path = Path("../data/documents")
    export_storage_path: Path = Path("../data/exports")
    backup_storage_path: Path = Path("../data/backups")

    max_upload_size_mb: int = 25
    allowed_file_extensions: list[str] = Field(
        default_factory=lambda: [".pdf", ".docx", ".txt", ".md"]
    )

    ai_provider: str = "local"
    ai_api_key: str | None = None
    embedding_model: str = "local-tfidf"
    top_k_results: int = 5
    min_relevance_score: float = 0.10

    log_level: str = "INFO"
    enable_metrics: bool = True

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("allowed_file_extensions", mode="before")
    @classmethod
    def parse_allowed_extensions(cls, value: object) -> object:
        if isinstance(value, str):
            return [
                extension.strip().lower()
                for extension in value.split(",")
                if extension.strip()
            ]
        return value

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def ensure_storage_directories(self) -> None:
        for directory in (
            self.document_storage_path,
            self.export_storage_path,
            self.backup_storage_path,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def validate_production_configuration(self) -> None:
        if not self.is_production:
            return

        insecure_values = {
            "development-only-secret-change-before-production",
            "replace-this-with-a-long-random-production-secret",
        }

        if self.secret_key in insecure_values or len(self.secret_key) < 32:
            raise RuntimeError(
                "Production requires a strong SECRET_KEY containing at least 32 characters."
            )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_production_configuration()
    return settings


settings = get_settings()