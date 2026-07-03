# Week 10 - AI Document Classification & Metadata Extraction

## Project Overview

AI-powered Document Control Assistant for construction documents.

### Features

- Upload PDF and DOCX files
- Automatic document classification
- Metadata extraction
- Confidence score generation
- Test dataset generation
- API interface using FastAPI

### Supported Document Types

- Drawing
- Specification
- Method Statement
- Material Submittal
- Shop Drawing
- Inspection Report
- Contract
- Meeting Minutes
- RFI

### Run

```bash
pip install -r requirements.txt
python scripts/generate_sample_dataset.py
python scripts/run_demo.py
uvicorn app.main:app --reload
```

Open:

http://127.0.0.1:8000/docs