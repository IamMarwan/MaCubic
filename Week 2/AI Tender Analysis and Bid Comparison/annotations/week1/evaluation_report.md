# Development benchmark evaluation

Benchmark: `development-v1`

- Precision: **100%** (30/30)
- Recall: **100%** (30/30)
- Source-row duplicate IDs (including the explicitly revised REQ-08): 1
- Omissions: 0; wrong values: 0; unsupported inferences: 0; invalid source references: 0
- Seeded conflicts flagged: 2/2
- Re-import: 0 inserted, 0 updated; register remains at 30 entries.

Precision is matched final register entries divided by final register entries. Recall is matched final register entries divided by annotated reference entries. A match requires exact description, category, mandatory/optional status, quantity, unit, threshold, deadline, revision, and expected source file/page after explicit unknown values are normalized to null. REQ-08's reference reflects the explicitly superseding amendment.

**Limit:** this fixed synthetic corpus uses tagged requirement rows. The score does not measure extraction quality on arbitrary tender PDFs, handwriting, scans, or prose.
