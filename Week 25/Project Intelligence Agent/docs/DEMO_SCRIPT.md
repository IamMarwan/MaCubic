# 15-minute final demonstration

## Preparation

From this project folder, run `python run.py demo` and `python run.py evaluate`. Keep the generated report, trace, and evaluation output available. The complete packaged demo report and trace are under `examples/`.

| Time | Demonstration |
|---|---|
| 0:00–1:00 | Introduce the fictional Harbour View Medical Centre dataset and state that no live model or external project system is connected. |
| 1:00–3:00 | Show the 12 linked records in `data/project.json`, including document types, dates, statuses, and relationships. |
| 3:00–5:00 | Run `python run.py demo`. Explain how the request is interpreted and converted into an investigation plan. |
| 5:00–7:00 | Open `outputs/latest_trace.json`. Walk through search, reads, relationship traversal, evidence assessment, and report generation. |
| 7:00–10:00 | Review report sections for RFI-017, Submittal-044, NCR-008, the commissioning dependency, and overdue Action A-14. Check each citation's document ID and source line. |
| 10:00–11:30 | Review V-026 and access-date conflict. Explain that conflicting records are surfaced without resolving entitlement or assigning fault. |
| 11:30–13:00 | Run `python run.py evaluate`; explain precision, recall, F1, exact scenario accuracy, citation coverage, and synthetic-data limits. |
| 13:00–14:00 | Start `python run.py serve`; show `GET /health` and a `POST /investigate` request with `curl` or an API client. |
| 14:00–15:00 | Close with human review, security limitations, and one next step: replace the simulated corpus with approved access-controlled records and independently reviewed evaluation labels. |

Example API call from another PowerShell window:

```powershell
$body = @{ request = "Analyze all major outstanding issues and management risks" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8080/investigate" -ContentType "application/json" -Body $body
```
