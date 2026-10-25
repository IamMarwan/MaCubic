# Security findings and mitigations

| Area | Demonstration control | Limitation |
|---|---|---|
| Authentication | API key mapped to `app` or `reviewer` role | Demo keys are known and not production credentials |
| Document isolation | Every document lookup filters by owner; hidden docs return 404 | Identity mapping is static configuration |
| Tool authorization | MCP tools call a shared ACL-checked service | Local stdio identity is provided by environment, not a remote IdP |
| Prompt injection | Configurable phrase signals block direct chat requests; suspicious document text is sent to mandatory review | Heuristic detection can miss or overflag attacks |
| Input abuse | Pydantic bounds and configurable character limits; search length bounds | Request-body byte limits should also be configured at ingress |
| Output validation | Provider output size and private-key marker checks | This is not a full semantic or DLP classifier |
| Human review | Configurable confidence bands and always-review high-risk actions | Reviewer identity lifecycle is demo-level |
| Audit | SQLite records gateway, tool, workflow, and approval events | Local DB is not tamper-proof and is not distributed |
| Rate limiting | Per-key rolling minute window | Memory-only; resets on restart and does not coordinate replicas |

Do not treat this project as production-hardened. Use managed identity, secret storage, durable append-only audit, centralized rate limiting, input and output DLP, dependency review, and security monitoring before production use.
