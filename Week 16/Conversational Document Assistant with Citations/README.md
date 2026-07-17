# Conversational Document Assistant with Citations

## Overview

This project was developed for **Week 16**.

The application provides a conversational interface for asking questions about uploaded documents while always returning supporting citations.

## Features

- FastAPI REST API
- Upload text documents
- Multi-document retrieval
- Conversation history
- Follow-up question support
- Source citations
- Graceful insufficient-information handling
- Automated tests

---

## Project Structure

```
app/
data/
tests/
README.md
requirements.txt
```

---

## Installation

```bash
python -m venv .venv
```

Windows

```bash
.venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run

```bash
uvicorn app.main:app --reload
```

Swagger

```
http://127.0.0.1:8000/docs
```

Run tests

```bash
pytest
```

---

## Example Workflow

1. Upload one or more documents.
2. Ask a question.
3. Receive:
   - Answer
   - Conversation ID
   - Source citations

---

## Example Response

```json
{
  "answer": "...",
  "conversation_id": 1,
  "citations": [
    {
      "document": "project_requirements.txt",
      "chunk": 2
    }
  ]
}
```

---

## Demonstrated Week 16 Requirements

- Improved retrieval quality
- Multi-document support
- Conversation history
- Source citations
- Graceful insufficient-information handling