# Verification results

Checked at 2026-09-13T09:56:32.055228+00:00 using Python 3.12.14.

- Automated suite: **55 tests passed**, 0 failures, 0 errors, 0 skipped.
- Actual HTTP demonstration: **17 of 17 scenario runs completed**, with expected outcomes asserted.
- All scenario executions used the **offline** planner.
- The OpenAI adapter was checked with injected API responses, including a different valid tool order, invalid responses and unavailable tools.
- Live OpenAI execution, a Docker build and browser rendering were **not verified** in this environment.
- Dashboard JavaScript passed the Node syntax check; dashboard/documentation routes passed HTTP tests.

## Scenario results

| Scenario | Task | Tools used | Actual result |
|---|---|---:|---|
| 01_complete_new_revision | workflow | 7 | route_for_review |
| 02_missing_checker | workflow | 7 | return_for_completion |
| 03_outdated_upload | workflow | 7 | request_latest_revision |
| 04_exact_duplicate | workflow | 7 | record_duplicate |
| 05_revision_label_conflict | workflow | 7 | resolve_revision_conflict |
| 06_material_missing_datasheet | review | 7 | return_for_completion |
| 07_rfi_first_issue | workflow | 7 | route_for_review |
| 08_method_missing_risk_assessment | review | 7 | return_for_completion |
| 09_minutes_summary_only | summarize | 1 | summary generated |
| 10_invoice_classification_only | classify | 1 | invoice |
| 11_unknown_document | workflow | 5 | manual_triage |
| 12_revision_lookup_only | revisions | 2 | new_revision |
| 13_conflicting_project_fields | workflow | 6 | return_for_completion |
| 14_invalid_issue_date | workflow | 7 | return_for_completion |
| 15_incomparable_revision_scheme | workflow | 7 | resolve_revision_conflict |
| 16_separate_project_register | workflow | 7 | route_for_review |
| 17_embedded_instruction | workflow | 7 | route_for_review |

## Reproduce

```powershell
python scripts/run_tests.py
python run.py
# In a second terminal:
python scripts/demo_client.py --all --assert-expected
```

## Captured evidence

- [Automated test report](evidence/test_report.json)
- [Live HTTP demonstration transcript](evidence/live_demo_transcript.txt)
- [All scenario execution results and events](evidence/all_scenarios.json)

The captured files are immutable snapshots of the preparation checks. New runs write to `outputs/` and do not overwrite these supplied snapshots. The data is fictional; these results are not a real-world accuracy benchmark.
