# AI Powered Document Register

Week 11 Assignment

## Overview

This project implements an AI-powered document repository capable of:

- Managing project documents
- Tracking document versions
- Storing metadata
- Performing metadata-based searches
- Performing semantic AI-powered searches
- Supporting natural language document queries
- Providing REST API endpoints through FastAPI

---

## Features

### Metadata Repository

Stores:

- Document Code
- Title
- Category
- Project Name
- Discipline
- Author
- Status
- Description
- Content

### Version Tracking

Every document modification creates a new version record including:

- Version Number
- Checksum
- File Name
- Upload Date
- Change Summary

### Traditional Search

Search using:

- Category
- Project
- Discipline
- Author
- Status

### Semantic Search

Uses:

- TF-IDF embeddings
- Cosine similarity

to find documents by meaning instead of exact keywords.

### Natural Language Search

Examples:

```text
show me approved structural drawings for tower a
```

```text
find draft architectural specifications
```

---

## Project Structure

```text
AI Powered Document Register/
│
├── app/
├── dataset/
├── docs/
├── scripts/
├── tests/
│
├── README.md
├── requirements.txt
└── .gitignore
```

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Seed Database

```bash
python -m app.seed
```

---

## Run API

```bash
uvicorn app.main:app --reload
```

---

## API Documentation

After launching:

```text
http://127.0.0.1:8000/docs
```

---

## Metadata Search Example

```http
GET /search/metadata?category=Drawing
```

---

## Semantic Search Example

```http
GET /search/semantic?query=concrete foundation structure
```

---

## Natural Language Search Example

```http
GET /search/natural?query=show me approved structural drawings for tower a
```

---

## Run Tests

```bash
python -m pytest
```

---

## Run Demo

```bash
python -m scripts.demo
```

---

## Technologies

- FastAPI
- SQLAlchemy
- SQLite
- Scikit-Learn
- TF-IDF
- Cosine Similarity
- Pytest

---

## Assignment Deliverables

✅ Search API

✅ Metadata Repository

✅ Document Version Tracking

✅ Semantic Search

✅ Natural Language Queries

✅ Traditional Metadata Search

✅ Automated Tests

✅ Demonstration Script