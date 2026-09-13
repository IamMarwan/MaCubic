"""Task boundaries and prerequisite checks, independent of the planner."""

from app.tools import TOOL_SPECS

TECHNICAL_TYPES = {"drawing", "material_submittal", "method_statement", "rfi", "inspection_request"}


def required_checks(state):
    needed = {"classify_document", "extract_metadata", "check_completeness"}
    kind = state.results.get("classify_document", {}).get("document_type", "unknown")
    fields = state.results.get("extract_metadata", {}).get("fields", {})
    if kind != "unknown" and all(fields.get(k) for k in ("project", "document_number", "revision")):
        needed.add("detect_previous_revisions")
    if kind in TECHNICAL_TYPES:
        needed.add("search_knowledge_base")
    return needed


def goal_tools(state):
    if state.task == "summarize":
        return {"generate_summary"}
    if state.task == "classify":
        return {"classify_document"}
    if state.task == "revisions":
        return {"extract_metadata", "detect_previous_revisions"}
    return required_checks(state) | {"generate_review_comments", "recommend_next_action"}


def can_finish(state):
    return goal_tools(state) <= state.results.keys()


def eligible_tools(state):
    if state.task in {"classify", "summarize", "revisions"}:
        scope = goal_tools(state)
    else:
        scope = set(TOOL_SPECS)
    result = []
    for name, spec in TOOL_SPECS.items():
        if name not in scope or name in state.results:
            continue
        required = set(spec["requires"])
        if name in {"generate_review_comments", "recommend_next_action"}:
            required |= required_checks(state)
        if name == "recommend_next_action":
            required.add("generate_review_comments")
        if required <= state.results.keys():
            result.append(name)
    return result
