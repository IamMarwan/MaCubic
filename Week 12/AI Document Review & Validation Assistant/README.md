# Week 12 Assignment — AI Document Review & Validation Assistant

## Project Overview

This project is an AI-assisted document review and validation system for Cubic Engineering Consultancy.

The assistant reviews uploaded documents before submission and checks for:

- Missing required information
- Unsupported document types
- Empty or incomplete content
- Missing dates
- Missing signatures
- Possible duplicate submissions
- Document summary generation
- Warnings and recommendations
- JSON and PDF review reports

---

## Week 12 Goal

Develop an AI assistant that reviews uploaded documents and identifies potential issues before submission.

---

## Deliverables Covered

| Deliverable | Status |
|---|---|
| Validation engine | Completed |
| Document review report | Completed |
| Duplicate detection capability | Completed |
| AI-generated document summaries | Completed |
| Demonstration of review workflow | Completed |

---

## Project Structure

```text
Week 12/
└── AI Document Review & Validation Assistant/
    ├── app.py
    ├── config.py
    ├── requirements.txt
    ├── README.md
    ├── validator/
    │   ├── __init__.py
    │   ├── models.py
    │   ├── file_utils.py
    │   ├── validation_rules.py
    │   ├── validation_engine.py
    │   ├── duplicate_detector.py
    │   ├── summarizer.py
    │   ├── reviewer.py
    │   └── report_generator.py
    ├── uploads/
    ├── reports/
    ├── sample_documents/
    ├── tests/
    │   ├── test_validation.py
    │   ├── test_duplicates.py
    │   └── test_summary.py
    └── demo/
        └── workflow_demo.py