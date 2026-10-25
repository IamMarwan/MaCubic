# Adversarial security results

## Before / after summary

| Stage | Result |
|---|---|
| Before controls | No baseline application run was available; the pre-control result is not measured. |
| After controls | Security checks and 25 adversarial test cases are implemented. Runtime results are not verified because required Python packages could not be installed in this environment (package index unavailable). |

The “Actual behavior” column records the execution status honestly; expected outcomes below describe the intended control behavior, not measured test results. Run `pytest -q` in the project virtual environment to populate verified results.

## Attack records

| # | Attack | Expected behavior | Actual behavior | Pass/Fail |
|---:|---|---|---|---|
| 1 | Direct override | Block detected instruction override and do not call provider. | Not run: runtime dependencies unavailable; expected policy is implemented. | Not verified |
| 2 | System prompt extraction | Block detected system-prompt extraction request. | Not run: runtime dependencies unavailable; expected policy is implemented. | Not verified |
| 3 | Approval bypass | Block request to bypass approval controls. | Not run: runtime dependencies unavailable; expected policy is implemented. | Not verified |
| 4 | Secret exfiltration | Block request to exfiltrate data. | Not run: runtime dependencies unavailable; expected policy is implemented. | Not verified |
| 5 | Credential request | Block request to send secrets. | Not run: runtime dependencies unavailable; expected policy is implemented. | Not verified |
| 6 | Prior rules override | Block attempt to override prior system rules. | Not run: runtime dependencies unavailable; expected policy is implemented. | Not verified |
| 7 | Role impersonation | Block detected system-role impersonation. | Not run: runtime dependencies unavailable; expected policy is implemented. | Not verified |
| 8 | Benign request | Allow normal summarization prompt. | Not run: runtime dependencies unavailable; expected policy is implemented. | Not verified |
| 9 | Ordinary classification | Allow a normal classification request. | Not run: runtime dependencies unavailable; expected policy is implemented. | Not verified |
| 10 | Quoted benign phrase | Do not flag ordinary wording unrelated to configured signals. | Not run: runtime dependencies unavailable; expected policy is implemented. | Not verified |
| 11 | Large body | Return HTTP 413 above configured input size. | Not run: runtime dependencies unavailable; endpoint validation is implemented. | Not verified |
| 12 | Unknown document | Return HTTP 404 without exposing document contents. | Not run: runtime dependencies unavailable; owner-scoped lookup is implemented. | Not verified |
| 13 | Cross-user document id | Return HTTP 404 for another user's document. | Not run: runtime dependencies unavailable; owner-scoped lookup is implemented. | Not verified |
| 14 | Unauthorized decision | Return HTTP 403 for non-reviewer decision attempt. | Not run: runtime dependencies unavailable; reviewer role check is implemented. | Not verified |
| 15 | Invalid action | Reject invalid decision/action values; no execution. | Not run: runtime dependencies unavailable; decision validation is implemented. | Not verified |
| 16 | Missing tool name | Reject unknown tool name. | Not run: runtime dependencies unavailable; tool dispatch uses an allowlist. | Not verified |
| 17 | Private key output | Reject output containing a private-key marker. | Not run: runtime dependencies unavailable; output marker validation is implemented. | Not verified |
| 18 | HTML injection | Treat markup as text; do not render/execute it in this API. | Not run: runtime dependencies unavailable; API returns JSON and output validation is implemented. | Not verified |
| 19 | SQL-like query | Use parameterized database operations; do not expand query into SQL. | Not run: runtime dependencies unavailable; DB queries use parameters. | Not verified |
| 20 | Format injection | Do not grant control or reveal protected state from template-like text. | Not run: runtime dependencies unavailable; prompt is not used for tool authorization. | Not verified |
| 21 | Nested document instruction | Flag configured injection phrase in retrieved document and route to review. | Not run: runtime dependencies unavailable; document analyzer uses configured signals. | Not verified |
| 22 | Tool escalation | Reject inaccessible document despite requested tool call. | Not run: runtime dependencies unavailable; document ownership is checked in shared tool service. | Not verified |
| 23 | Prompt delimiter | Do not treat delimiter text as an authorization change. | Not run: runtime dependencies unavailable; tool permissions are enforced outside model text. | Not verified |
| 24 | Extreme unicode | Do not use Unicode controls to grant permissions. | Not run: runtime dependencies unavailable; authorization is role-based. | Not verified |
| 25 | Oversized tool query | Return HTTP 422 for search query above 300 characters. | Not run: runtime dependencies unavailable; search length validation is implemented. | Not verified |

## Before versus after controls

| Attack class | Before controls (baseline) | After controls (implemented behavior) |
|---|---|---|
| Prompt injection | No gateway filter in baseline design; behavior not measured. | Configured phrase matches are blocked and logged; detection remains heuristic. |
| Cross-user access | No owner filter in baseline design; behavior not measured. | Shared document service filters every lookup by owner; inaccessible documents return 404. |
| Reviewer action | No approval role gate in baseline design; behavior not measured. | Decision endpoint requires reviewer role and pending approval. |
| Oversized input | No configured bounds in baseline design; behavior not measured. | Character bounds and query limits reject oversized input. |
| Tool execution | No tool ACL in baseline design; behavior not measured. | MCP tool allowlist uses shared role/document access checks. |

These are implementation comparisons, not an empirical before/after penetration-test score.
