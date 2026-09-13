"""Small, explicit configuration; environment values override .env."""

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_env(path: Path) -> None:
    if path.is_file():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


@dataclass(frozen=True)
class Settings:
    provider: str = "offline"
    model: str = "gpt-4.1-mini"
    api_key: str = ""
    host: str = "127.0.0.1"
    port: int = 8000
    database: Path = ROOT / "outputs" / "agent.db"
    knowledge_base: Path = ROOT / "data" / "knowledge_base.json"
    max_upload_bytes: int = 10 * 1024 * 1024
    max_text_chars: int = 60000
    max_pages: int = 25
    max_steps: int = 12
    request_timeout: float = 30.0
    run_timeout: float = 180.0

    def __post_init__(self):
        if self.provider not in {"offline", "openai"}:
            raise ValueError("AGENT_PROVIDER must be offline or openai.")
        if self.provider == "openai" and not self.api_key.strip():
            raise ValueError("OPENAI_API_KEY is required for openai mode.")
        if not 1 <= self.max_steps <= 20:
            raise ValueError("MAX_AGENT_STEPS must be between 1 and 20.")
        if not 0 <= self.port <= 65535:
            raise ValueError("PORT must be between 0 and 65535.")
        if min(self.request_timeout, self.run_timeout) <= 0:
            raise ValueError("Timeouts must be positive.")

    @classmethod
    def from_env(cls):
        load_env(ROOT / ".env")
        return cls(
            provider=os.getenv("AGENT_PROVIDER", "offline").lower(),
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            api_key=os.getenv("OPENAI_API_KEY", ""),
            host=os.getenv("HOST", "127.0.0.1"),
            port=int(os.getenv("PORT", "8000")),
            database=Path(os.getenv("DATABASE_PATH", str(ROOT / "outputs" / "agent.db"))),
            max_steps=int(os.getenv("MAX_AGENT_STEPS", "12")),
            request_timeout=float(os.getenv("MODEL_TIMEOUT_SECONDS", "30")),
            run_timeout=float(os.getenv("RUN_TIMEOUT_SECONDS", "180")),
        )
