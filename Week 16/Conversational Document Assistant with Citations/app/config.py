from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = f"sqlite:///{BASE_DIR / 'document_assistant.db'}"

APP_NAME = "Conversational Document Assistant with Citations"

CHUNK_SIZE = 700
CHUNK_OVERLAP = 120
TOP_K_RESULTS = 4

MIN_RELEVANCE_SCORE = 0.18