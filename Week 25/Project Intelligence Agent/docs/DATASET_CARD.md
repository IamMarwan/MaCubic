# Dataset card

**Name:** Harbour View Medical Centre — Simulated Project  
**Purpose:** Demonstrate linked-document investigation, issue extraction, citations, conflict handling, and management reporting.  
**As-of date:** 30 October 2026.  
**Documents:** 12 fictional construction records covering contract, specification, RFI, submittal, coordination minutes, inspection, progress, correspondence, commercial register, site access log, and baseline schedule.  
**Evaluation:** 10 synthetic labeled requests in `data/evaluation.json`.

All project names, people, dates, amounts, and records are fictional. The AED 250,000 amount is a fabricated example. The dataset deliberately contains unresolved and conflicting records. A conflict signals a need for human review; it is not a finding of fault, entitlement, breach, or liability.

The project JSON stores source text as newline-separated lines. Citations use one-based line numbering within each document's `text` field. Dataset signals provide the structured labels used by this deterministic teaching implementation; they are not hidden from or inferred by an LLM.
