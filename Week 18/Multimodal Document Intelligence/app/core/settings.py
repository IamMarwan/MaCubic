"""Central application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Validated configuration for the document intelligence service."""

    app_name: str = "Multimodal Document Intelligence"
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = Field(default=8000, ge=1, le=65535)
    log_level: str = "INFO"

    vision_provider: Literal["mock", "openai"] = "mock"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    openai_timeout_seconds: int = Field(default=120, ge=10, le=600)

    pdf_render_dpi: int = Field(default=150, ge=72, le=400)
    max_pdf_pages: int = Field(default=50, ge=1, le=500)
    max_upload_size_mb: int = Field(default=25, ge=1, le=500)

    min_confidence: float = Field(default=0.50, ge=0.0, le=1.0)
    save_page_images: bool = True
    save_extraction_results: bool = True

    sample_documents_dir: Path = Path("data/sample_documents")
    sample_pages_dir: Path = Path("data/sample_pages")
    ground_truth_dir: Path = Path("data/ground_truth")
    extractions_dir: Path = Path("outputs/extractions")
    comparisons_dir: Path = Path("outputs/comparisons")
    reports_dir: Path = Path("outputs/reports")

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def max_upload_size_bytes(self) -> int:
        """Return the configured upload limit in bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    def resolve_path(self, path: Path) -> Path:
        """Resolve a configured path relative to the project root."""
        return path if path.is_absolute() else PROJECT_ROOT / path

    def create_directories(self) -> None:
        """Create all configured data and output directories."""
        directories = (
            self.sample_documents_dir,
            self.sample_pages_dir,
            self.ground_truth_dir,
            self.extractions_dir,
            self.comparisons_dir,
            self.reports_dir,
        )

        for directory in directories:
            self.resolve_path(directory).mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Return one cached settings instance."""
    return Settings()