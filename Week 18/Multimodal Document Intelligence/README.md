# Week 18 — Multimodal Document Intelligence

A standalone document-processing service that analyzes PDF pages both
textually and visually. It is designed for complex business and construction
documents containing title blocks, tables, drawing notes, stamps, revision
information, symbols, and visual annotations.

## Week 18 Objective

Traditional PDF extraction reads only the embedded text layer. This prototype
also renders each PDF page as an image and sends the rendered page to a
vision-capable analysis provider.

The service compares both methods and identifies information that visual
analysis recovers but normal PDF text extraction misses.

## Features

- PDF upload validation
- PDF text-layer extraction
- PDF page rendering to PNG
- Vision-capable page analysis
- Local deterministic visual-analysis mode
- OpenAI multimodal-analysis mode
- Title-block extraction
- Table extraction
- Drawing-note extraction
- Stamp and seal detection
- Revision-information extraction
- Symbol and visual-annotation extraction
- Confidence scores
- Page-number tracking
- Textual and visual evidence
- Normalized evidence bounding boxes
- Text-only versus multimodal comparison
- Structured JSON API
- Twenty generated construction-document test files
- Ground-truth evaluation data
- Automated accuracy and limitations report
- Automated tests
- Interactive Swagger API documentation
- Docker support

## Project Structure

```text
Multimodal Document Intelligence/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── logging.py
│   │   └── settings.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── services/
│   │   ├── comparison_service.py
│   │   ├── document_service.py
│   │   ├── mock_vision_provider.py
│   │   ├── openai_vision_provider.py
│   │   ├── pdf_processor.py
│   │   ├── provider_factory.py
│   │   ├── text_extractor.py
│   │   └── vision_provider.py
│   ├── utils/
│   │   └── __init__.py
│   ├── __init__.py
│   └── main.py
├── config/
│   └── extraction_categories.json
├── data/
│   ├── ground_truth/
│   ├── sample_documents/
│   └── sample_pages/
├── outputs/
│   ├── comparisons/
│   ├── extractions/
│   └── reports/
├── scripts/
│   ├── demo_client.py
│   ├── evaluate_accuracy.py
│   └── generate_test_documents.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_comparison_service.py
│   ├── test_mock_vision_provider.py
│   ├── test_pdf_processor.py
│   └── test_text_extractor.py
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── requirements.txt
└── run.py
```

## Processing Workflow

1. The API receives a PDF upload.
2. The service validates its extension, signature, size, encryption state,
   and page count.
3. PyMuPDF extracts each page's embedded text.
4. PyMuPDF renders each page as a PNG image.
5. The text-only extractor applies structured field rules to the text layer.
6. The selected vision provider analyzes the rendered page.
7. The service validates and filters extracted items by confidence.
8. Both extraction methods are compared by page, category, and field name.
9. JSON results are returned and optionally saved under `outputs/`.

## Requirements

- Python 3.11 or 3.12
- pip
- An OpenAI API key only when using the real OpenAI provider

The default mock provider does not require an API key.

## Local Setup

Open PowerShell in the project directory:

```powershell
cd "C:\Users\Dell\Desktop\MaCubic\Week 18\Multimodal Document Intelligence"
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

Install the dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create the local environment file:

```powershell
Copy-Item ".env.example" ".env"
```

The default configuration is:

```env
VISION_PROVIDER=mock
OPENAI_API_KEY=
```

No API key is required in mock mode.

## Generate the 20 Test Documents

Run:

```powershell
python scripts/generate_test_documents.py
```

This creates:

- 20 one-page construction PDF documents
- 20 matching ground-truth JSON files
- Visual-only red stamps
- Visual-only blue annotations
- Visual construction symbols
- Embedded title-block, revision, note, and table text

## Run the Automated Tests

```powershell
pytest -v
```

## Generate the Accuracy Report

```powershell
python scripts/evaluate_accuracy.py
```

Generated reports:

```text
outputs/reports/accuracy_report.md
outputs/reports/accuracy_results.json
```

The report contains:

- Document and page counts
- Text-only precision, recall, and F1 score
- Multimodal precision, recall, and F1 score
- Visual-recovery precision, recall, and F1 score
- Per-document results
- Identified limitations
- Reproduction commands

## Start the API

```powershell
python run.py
```

Alternative command:

```powershell
uvicorn app.main:app --reload
```

Open the interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

Health endpoint:

```text
http://127.0.0.1:8000/api/v1/health
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Service information |
| `GET` | `/api/v1/health` | Provider and application health |
| `POST` | `/api/v1/extract` | Structured multimodal extraction |
| `POST` | `/api/v1/compare` | Text-only versus multimodal comparison |
| `POST` | `/api/v1/analyze` | Complete combined analysis |

## Demonstration

First start the API:

```powershell
python run.py
```

Open a second PowerShell terminal, activate the same environment, and run:

```powershell
python scripts/demo_client.py
```

The demonstration uses `construction_test_12.pdf`, which contains a title
block, revision information, notes, a table, a red stamp, blue markup, and a
construction symbol.

The full demonstration JSON is saved to:

```text
outputs/extractions/demo_result.json
```

## Example Structured Item

```json
{
  "category": "stamp",
  "field_name": "visual_stamp",
  "value": "Red stamp or seal detected",
  "confidence": 0.88,
  "page_number": 1,
  "method": "multimodal",
  "evidence": {
    "quote": "",
    "description": "A concentrated red-colored region was detected on the rendered page.",
    "bounding_box": {
      "x1": 0.61,
      "y1": 0.33,
      "x2": 0.82,
      "y2": 0.51
    }
  },
  "visually_recovered": true
}
```

## Use the Real OpenAI Vision Provider

Create `.env` from `.env.example` if it does not already exist:

```powershell
Copy-Item ".env.example" ".env"
```

Open `.env` and change these two values:

```env
VISION_PROVIDER=openai
OPENAI_API_KEY=YOUR_REAL_OPENAI_API_KEY
```

Replace `YOUR_REAL_OPENAI_API_KEY` with the actual API key.

Never place a real key in `.env.example`, source code, screenshots, or GitHub.
The `.env` file is excluded by `.gitignore`.

Then restart the API:

```powershell
python run.py
```

## Docker

Build the image:

```powershell
docker build -t multimodal-document-intelligence .
```

Run in mock mode:

```powershell
docker run --rm -p 8000:8000 multimodal-document-intelligence
```

Run using configuration from `.env`:

```powershell
docker run --rm -p 8000:8000 --env-file .env multimodal-document-intelligence
```

## Security and Validation

The service:

- Accepts only PDF uploads
- Checks the PDF file signature
- Rejects empty documents
- Rejects password-protected PDFs
- Enforces upload-size and page-count limits
- Keeps API credentials outside source code
- Uses stable document identifiers derived from file content
- Normalizes model-produced bounding boxes and confidence values

## Known Limitations

- The bundled dataset is synthetic rather than a collection of confidential
  real-world construction documents.
- The mock provider uses deterministic color analysis and does not represent
  the full reasoning ability of a vision-language model.
- Complex merged tables may require specialized table-recognition logic.
- Handwriting quality, scan resolution, and page rotation affect extraction.
- Symbols may require discipline-specific symbol libraries.
- Very large drawings may require page tiling to retain small visual details.
- Real-model cost and processing time vary by model, resolution, and page
  count.
- Human review remains necessary for safety-critical engineering decisions.

## Intended Use

This repository is an educational prototype demonstrating multimodal document
intelligence beyond traditional text extraction and RAG. It should not be used
as the sole authority for construction approval, regulatory compliance, or
engineering decisions.