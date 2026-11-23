# Week 2 benchmark evaluation

- Labeled bidder-requirement pairs: **90**
- Exact status agreement: **90/90 (100.0%)**
- Deviation findings: **37**; clarification questions: **50**

## Per-status results

| Status | Support | Correct | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| met | 36 | 36 | 100.0% | 100.0% | 100.0% |
| partially met | 21 | 21 | 100.0% | 100.0% | 100.0% |
| not met | 12 | 12 | 100.0% | 100.0% | 100.0% |
| not evidenced | 17 | 17 | 100.0% | 100.0% | 100.0% |
| not applicable | 4 | 4 | 100.0% | 100.0% | 100.0% |

## Confusion matrix

Rows are manual labels; columns are predicted statuses.

| Expected \ Predicted | met | partially met | not met | not evidenced | not applicable |
|---|---:|---:|---:|---:|---:|
| met | 36 | 0 | 0 | 0 | 0 |
| partially met | 0 | 21 | 0 | 0 | 0 |
| not met | 0 | 0 | 12 | 0 | 0 |
| not evidenced | 0 | 0 | 0 | 17 | 0 |
| not applicable | 0 | 0 | 0 | 0 | 4 |

## Adversarial checks

- `paraphrase_delivery`: PASS (expected REQ-16; got REQ-16).
- `paraphrase_warranty`: PASS (expected REQ-23; got REQ-23).
- `contradiction`: PASS (expected not evidenced; got not evidenced).
- `omitted_answer`: PASS (expected not evidenced; got not evidenced).
- `irrelevant_attachment`: PASS (expected not evidenced; got not evidenced).

## Acceptance checks

- Seeded exclusion: surfaced (`cedar_build::REQ-04`).
- Seeded alternative proposal: surfaced (`cedar_build::REQ-11`).
- Seeded delivery deviation: surfaced (`northstar_works::REQ-16`).
- Seeded warranty gap: surfaced (`summit_contracting::REQ-23`).
- Seeded contradiction: surfaced (`summit_contracting::REQ-20`).
- Mandatory met findings without bid evidence: 0.
- Missing tender source references: 0.
- Unsupported substantive bid findings: 0.

**Method:** Stable requirement IDs are preferred when present. ID-free passages are mapped by normalized token overlap, curated terminology synonyms, and fuzzy phrase similarity. Status decisions use explicit commitments, limitations, refusals, justified scope exclusions, and contradictory passages; ambiguous or absent evidence is not evidenced.

**Limit:** Results are for a synthetic, manually labeled package and a transparent rule-based baseline; they do not establish accuracy on arbitrary or real-world tender submissions.
