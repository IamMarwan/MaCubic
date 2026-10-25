import json, os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

def read_json(relative: str):
    with (ROOT / relative).open(encoding="utf-8") as handle:
        return json.load(handle)

APP_KEYS = json.loads(os.getenv("APP_KEYS_JSON", '{"demo-app-key":{"role":"app","user_id":"user-1"},"demo-reviewer-key":{"role":"reviewer","user_id":"user-1"}}'))
DB_PATH = os.getenv("APP_DB_PATH", str(ROOT / "data" / "workflow.db"))
SECURITY = read_json("configs/security.json")
RATE_LIMIT = int(os.getenv("APP_RATE_LIMIT_PER_MINUTE", SECURITY["rate_limit_per_minute"]))
MAX_INPUT = int(os.getenv("APP_MAX_INPUT_CHARS", SECURITY["max_input_chars"]))
