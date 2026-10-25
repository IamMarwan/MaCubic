# Ten demonstration scenarios

1. Send a classification request to `/v1/gateway/chat`; inspect chosen model and estimated tokens/cost.
2. Disable the preferred model in `configs/models.json`; repeat and observe configured fallback.
3. Submit `DOC-100`; confirm 72% confidence routes to the approval queue.
4. Approve the pending classification as reviewer and confirm execution status.
5. Modify the proposed action, then approve; inspect the resulting audit entry.
6. Reject a pending action and confirm it is not executed.
7. Submit `DOC-102` (88% confidence) and observe automatic processing under the configured threshold.
8. Search documents as `user-1`; verify `DOC-200` owned by `user-2` is not returned.
9. Use MCP `compare_revisions` on `DOC-100` and `DOC-101`; inspect the unified diff.
10. Submit a prompt-injection phrase and an oversized prompt; verify security policy blocks each and records the relevant event.

MCP server: `python mcp_server.py`. MCP client demo: `python scripts/mcp_demo_client.py`. API docs: `/docs`. The committed dataset and scorecard are demonstration data.
