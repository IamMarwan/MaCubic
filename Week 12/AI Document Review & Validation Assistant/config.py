from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = BASE_DIR / "uploads"
REPORT_DIR = BASE_DIR / "reports"
SAMPLE_DOCUMENT_DIR = BASE_DIR / "sample_documents"

UPLOAD_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)
SAMPLE_DOCUMENT_DIR.mkdir(exist_ok=True)

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt"
}

MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

DUPLICATE_THRESHOLD = 85

REQUIRED_FIELDS = [
    "title",
    "author",
    "date",
    "signature"
]

PASS = "PASS"
WARNING = "WARNING"
FAIL = "FAIL"