# AI Document Relationships & Knowledge Graph

## Overview

This project extends the AI Document Control Assistant by introducing document relationships and a simple knowledge graph. The system automatically identifies connections between project documents, stores those relationships, and provides API endpoints to retrieve related documents.

The application demonstrates how engineering documents such as RFIs, drawings, specifications, and meeting minutes can be connected to improve document navigation and project understanding.

---

## Features

- Detect relationships between project documents.
- Link RFIs to referenced drawings and specifications.
- Link meeting minutes to action items and referenced documents.
- Store document relationships in a SQLite database.
- Build a document relationship graph.
- Retrieve related documents through REST API endpoints.
- Simple graph visualization page.

---

## Technologies

- Python 3.12+
- FastAPI
- SQLAlchemy
- SQLite
- NetworkX
- Pytest

---

## Project Structure

```text
AI Document Relationships Knowledge Graph/
│
├── app/
│   ├── api/
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── relationship_engine.py
│   ├── sample_data.py
│   └── schemas.py
│
├── static/
│   └── graph_viewer.html
│
├── tests/
│   └── test_relationship_engine.py
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Installation

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Run

```bash
uvicorn app.main:app --reload
```

API documentation:

```
http://127.0.0.1:8000/docs
```

Relationship Viewer:

```
http://127.0.0.1:8000/graph
```

---

## Week 15 Deliverables

- Document Relationship Engine
- Knowledge Graph
- Relationship Viewer
- Related Document API
- Sample Engineering Documents
- Automated Tests

---

## Author

Marwan