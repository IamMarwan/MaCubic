# Dataset card — cubic-document-eval-v1

- **Purpose:** Training assignment for structured document-AI evaluation.
- **Origin:** Fictional scenarios authored for this package and reproducibly rendered by `scripts/build_dataset.py`; no real company documents.
- **Size:** 30 corpus documents; 105 cases; 40 local classifier training texts.
- **Splits:** 35 development / 70 test cases, grouped by project. Shared source templates create correlation across splits.
- **Tasks:** 57 QA, 24 metadata, 24 classification. Test split: 38 / 16 / 16.
- **Categories:** Drawing, RFI, material submittal, method statement, inspection request, meeting minutes, invoice, transmittal.
- **Cases:** Alternate field labels, missing values, colliding references across projects, superseded/current revisions, similar numbers, explicit unanswerability, multi-document comparison and a quoted instruction.
- **Annotation:** Gold values and exact source lines are generated together and cross-checked. Human expert validation and independent production sampling have not been performed.
- **Exclusions:** PDF/OCR, multilingual content, scanned handwriting, unrestricted answer prose, real engineering approvals, arbitrary agent tool execution.
- **Leakage controls:** Different training/evaluation texts; providers see only allowlisted inputs and source text, never facts or gold cases. This is an interface guarantee, not process isolation.
- **Versioning:** Full corpus, case, fact and training content is hashed per run. Any change creates a different benchmark identity and blocks direct comparison to older results.
- **Recommended next validation:** Freeze a prompt on development data, add independently reviewed authorized project records, separate projects/time periods, and measure inter-annotator agreement.

Rebuild with `python scripts/build_dataset.py`. The checked-in JSON files are the runnable benchmark; rebuilding is optional.
