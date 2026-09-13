# Live demonstration script

Allow about five minutes for the offline demonstration. Real model runs may
take longer depending on API response times.

1. Start `python run.py` and open the dashboard. Point out the planner mode.
2. In a second terminal, run `python scripts/demo_client.py`. This indexes
   revision 01 and runs three documents through the actual HTTP API.
3. Open the complete drawing in history. Show metadata, the previous revision,
   the actual text diff in the JSON, completeness checks and the final action.
4. Open the missing-checker drawing. Show the missing field and the changed
   next action: `return_for_completion`.
5. Open the summary-only run. Show that just one of the eight tools executed.
6. Expand complete history to show timestamps, decisions, arguments, tool
   results, elapsed time and stop reason. Refresh the page to demonstrate
   that history persists in SQLite.
7. To demonstrate an LLM making the tool decisions, configure `openai` in
   `.env`, restart the service, and repeat the three-case demo. Show the
   `openai` provider/model fields in the actual new run results.

Use accurate language during the demo: offline mode demonstrates the
orchestration framework and adaptive rules; model mode demonstrates the model
choosing tools. A replayed offline result is not a live model demonstration.

For all 17 regression scenarios:

```powershell
python scripts/demo_client.py --all --assert-expected
```

For a failure demonstration, temporarily set `MAX_AGENT_STEPS=1`, restart,
and submit a full workflow task. The run halts with `step_limit` and keeps its
partial results. Restore `MAX_AGENT_STEPS=12` afterward.
