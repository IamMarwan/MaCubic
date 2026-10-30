# Security and human oversight

- The sample server binds to `127.0.0.1` by default. Do not expose it to a network without adding TLS, network controls, identity integration, and a production server.
- Set `PROJECT_AGENT_TOKEN` to require a bearer token for `POST /investigate`. The token is read from the process environment and is never returned or logged.
- Request bodies are limited to 16 KiB; request text is limited to 2,000 characters. Unknown paths and invalid JSON receive structured errors.
- The agent treats document text as evidence data. It has no tool for changing records, sending email, approving submissions, or executing recommendations.
- A human must validate every inference, citation, conflicting statement, and recommendation before operational use. No unsupported finding should be promoted as fact.
- The demo has no user database, role-based document access, encryption at rest, audit retention policy, or real project connector. These are production gaps, not implemented features.

Environment variables:

| Name | Default | Purpose |
|---|---|---|
| `PROJECT_AGENT_HOST` | `127.0.0.1` | Bind address |
| `PROJECT_AGENT_PORT` | `8080` | HTTP port |
| `PROJECT_AGENT_TOKEN` | unset | Optional bearer token for investigation requests |
