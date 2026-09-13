"""Eight real tools. Every finding is tied to observed fields or register records.

These tools are deterministic. In openai mode the model chooses when to call
them; the offline planner is a reproducible policy baseline, not an LLM.
"""

import difflib
import json
import re
from datetime import date

from app.models import InputError

TYPE_PATTERNS = {
    "drawing": r"\b(shop drawing|construction drawing|drawing number)\b",
    "material_submittal": r"\b(material submittal|material approval request)\b",
    "rfi": r"\b(request for information|rfi)\b",
    "method_statement": r"\b(method statement)\b",
    "inspection_request": r"\b(inspection request|work inspection request)\b",
    "meeting_minutes": r"\b(meeting minutes|minutes of meeting)\b",
    "invoice": r"\b(invoice)\b",
}
ALIASES = {
    "project": ["project", "project name"],
    "document_number": ["document number", "document no", "drawing number", "rfi number", "invoice number"],
    "title": ["title", "document title", "subject"],
    "revision": ["revision", "rev"],
    "date": ["date", "issue date"],
    "discipline": ["discipline"],
    "prepared_by": ["prepared by", "author"],
    "checked_by": ["checked by", "reviewed by"],
    "supplier": ["supplier", "vendor"],
    "product": ["product", "material"],
    "datasheet": ["datasheet", "data sheet"],
    "question": ["question", "clarification required"],
    "response_due": ["response due", "required by"],
    "scope": ["scope"],
    "procedure": ["procedure", "method"],
    "risk_assessment": ["risk assessment"],
    "location": ["location"],
    "inspection_date": ["inspection date"],
    "attendees": ["attendees"],
    "actions": ["actions", "action items"],
    "amount": ["amount", "total"],
    "purchase_order": ["purchase order", "po number"],
}
COMMON = ["project", "document_number", "title", "revision", "date"]
REQUIRED = {
    "drawing": COMMON + ["discipline", "prepared_by", "checked_by"],
    "material_submittal": COMMON + ["supplier", "product", "datasheet"],
    "rfi": COMMON + ["question", "response_due"],
    "method_statement": COMMON + ["scope", "procedure", "risk_assessment"],
    "inspection_request": COMMON + ["location", "inspection_date"],
    "meeting_minutes": COMMON + ["attendees", "actions"],
    "invoice": COMMON + ["supplier", "amount", "purchase_order"],
    "unknown": COMMON,
}


def usable(value):
    return bool(value.strip()) and value.strip().lower() not in {
        "n/a", "na", "none", "missing", "tbd", "pending", "not provided", "-", "not attached"
    }


def extract_fields(document):
    values, evidence, conflicts = {}, {}, {}
    for field, aliases in ALIASES.items():
        pattern = re.compile(r"^\s*(?:" + "|".join(map(re.escape, aliases)) + r")\s*[:=]\s*(.*?)\s*$", re.I)
        matches = []
        for number, line in document.lines:
            match = pattern.match(line)
            if match and usable(match.group(1)):
                value = match.group(1).strip()
                matches.append(value)
                evidence.setdefault(field, []).append({"line": number, "quote": line})
        unique = list(dict.fromkeys(matches))
        if len({v.casefold() for v in unique}) > 1:
            conflicts[field] = unique
        elif unique:
            values[field] = unique[0]
    return {"fields": values, "evidence": evidence, "conflicts": conflicts,
            "method": "labelled-field extraction", "source": document.filename}


def revision_key(value):
    """Compare numeric, letters, or prefix-number revisions within one scheme."""
    value = re.sub(r"^(?:revision|rev)\s*[:.]?\s*", "", value.strip(), flags=re.I).upper()
    if re.fullmatch(r"\d+", value):
        return "numeric", int(value)
    if re.fullmatch(r"[A-Z]+", value):
        number = 0
        for char in value:
            number = number * 26 + ord(char) - ord("A") + 1
        return "alphabetic", number
    match = re.fullmatch(r"([A-Z]+)(\d+)", value)
    if match:
        return match.group(1), int(match.group(2))
    return None


class DocumentTools:
    def __init__(self, repository, knowledge_base):
        self.repository = repository
        self.knowledge_base = knowledge_base

    def classify_document(self, state, **_):
        # Prefer the declared type or heading; references in body text do not
        # override an unambiguous declared type.
        lines = state.document.lines
        headings = [(n, line) for n, line in lines if line.strip()][:3]
        declarations = [(n, line) for n, line in lines if re.match(r"\s*document type\s*:", line, re.I)]
        candidates = declarations or headings
        matches = []
        for kind, pattern in TYPE_PATTERNS.items():
            for number, line in candidates:
                if re.search(pattern, line, re.I):
                    matches.append((kind, {"line": number, "quote": line}))
                    break
        kinds = sorted({kind for kind, _ in matches})
        return {"document_type": kinds[0] if len(kinds) == 1 else "unknown",
                "candidates": kinds, "ambiguous": len(kinds) > 1,
                "evidence": [e for _, e in matches], "method": "document heading rules"}

    def extract_metadata(self, state, **_):
        return extract_fields(state.document)

    def search_knowledge_base(self, state, query="", **_):
        kind = state.results["classify_document"]["document_type"]
        fields = state.results["extract_metadata"]["fields"]
        if not query:
            query = f"{kind.replace('_', ' ')} {fields.get('title', '')} {state.instruction}"
        tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
        records = json.loads(self.knowledge_base.read_text(encoding="utf-8"))
        matches = []
        for record in records:
            if record.get("project") and record["project"].casefold() != fields.get("project", "").casefold():
                continue
            if kind not in record["document_types"]:
                continue
            haystack = " ".join([record["title"], record["text"], *record.get("keywords", [])]).lower()
            score = len(tokens & set(re.findall(r"[a-z0-9]+", haystack)))
            if score:
                matches.append({**record, "score": score})
        matches.sort(key=lambda item: (-item["score"], item["id"]))
        return {"query": query, "matches": matches[:3], "method": "type-filtered lexical search",
                "scope": "Bundled fictional training requirements; not external engineering standards."}

    def check_completeness(self, state, **_):
        kind = state.results["classify_document"]["document_type"]
        metadata = state.results["extract_metadata"]
        fields = metadata["fields"]
        required = REQUIRED[kind]
        missing = [name for name in required if name not in fields]
        invalid = []
        for field in ("date", "response_due", "inspection_date"):
            if field in fields:
                try:
                    date.fromisoformat(fields[field])
                except ValueError:
                    invalid.append({"field": field, "message": "Use a valid ISO date: YYYY-MM-DD."})
        if fields.get("revision") and revision_key(fields["revision"]) is None:
            invalid.append({"field": "revision", "message": "Revision label cannot be ordered reliably."})
        return {"complete": not (missing or invalid or metadata["conflicts"]),
                "required_fields": required, "missing_fields": missing,
                "invalid_fields": invalid, "conflicts": metadata["conflicts"],
                "scope": "Declared metadata only; attachments, signatures and engineering correctness are not verified."}

    def detect_previous_revisions(self, state, **_):
        fields = state.results["extract_metadata"]["fields"]
        missing = [key for key in ("project", "document_number", "revision") if key not in fields]
        if missing:
            return {"status": "not_checkable", "missing_fields": missing, "previous": None}
        current = revision_key(fields["revision"])
        if current is None:
            return {"status": "unorderable", "previous": None, "reason": "Unsupported revision label."}
        records = self.repository.revisions(fields["project"], fields["document_number"])
        previous, newer, same, incomparable = [], [], [], []
        for record in records:
            key = revision_key(record["revision"])
            if key is None or key[0] != current[0]:
                incomparable.append(record)
            elif key[1] < current[1]:
                previous.append(record)
            elif key[1] > current[1]:
                newer.append(record)
            else:
                same.append(record)

        def public(record):
            return {key: record[key] for key in ("id", "revision", "filename", "sha256")}

        previous.sort(key=lambda r: revision_key(r["revision"])[1], reverse=True)
        old = previous[0] if previous else None
        identical = [r for r in same if r["sha256"] == state.document.sha256]
        conflicts = [r for r in same if r["sha256"] != state.document.sha256]
        if newer:
            status = "superseded"
        elif conflicts:
            status = "revision_conflict"
        elif incomparable:
            status = "unorderable"
        elif identical:
            status = "duplicate"
        elif old:
            status = "new_revision"
        else:
            status = "first_issue"
        diff = list(difflib.unified_diff(old["text"].splitlines(), state.document.text.splitlines(),
                                       fromfile=old["filename"], tofile=state.document.filename, lineterm="")) if old else []
        return {"status": status, "current_revision": fields["revision"],
                "previous": public(old) if old else None,
                "newer": [public(r) for r in newer], "same_revision_conflicts": [public(r) for r in conflicts],
                "incomparable": [public(r) for r in incomparable], "diff": diff[:80],
                "diff_truncated": len(diff) > 80,
                "scope": "Same project and document number in the explicitly indexed local register."}

    def generate_summary(self, state, **_):
        # Extractive output preserves source wording and includes line evidence.
        candidates = [(n, line.strip()) for n, line in state.document.lines if line.strip()]
        selected = candidates[:2]
        signals = r"\b(scope|question|action|change|revision|risk|issue|subject|title|procedure)\b"
        for pair in candidates[2:]:
            if re.search(signals, pair[1], re.I) and len(selected) < 7:
                selected.append(pair)
        if len(selected) < 4:
            for pair in candidates:
                if pair not in selected and len(selected) < 4:
                    selected.append(pair)
        selected.sort()
        return {"method": "extractive", "source": state.document.filename,
                "points": [{"line": n, "quote": line[:600], "truncated": len(line) > 600}
                           for n, line in selected]}

    def generate_review_comments(self, state, **_):
        checks = state.results["check_completeness"]
        fields = state.results["extract_metadata"]["fields"]
        comments = []
        for field in checks["missing_fields"]:
            comments.append({"severity": "major", "code": "MISSING_FIELD", "field": field,
                             "comment": f"Provide {field.replace('_', ' ')}.", "source": "check_completeness"})
        for field, values in checks["conflicts"].items():
            comments.append({"severity": "major", "code": "CONFLICTING_METADATA", "field": field,
                             "comment": f"Resolve conflicting values: {', '.join(values)}.",
                             "source": "extract_metadata", "evidence": state.results["extract_metadata"]["evidence"][field]})
        for issue in checks["invalid_fields"]:
            comments.append({"severity": "major", "code": "INVALID_FIELD", **issue,
                             "comment": issue["message"], "source": "check_completeness"})
        revision = state.results.get("detect_previous_revisions", {})
        if revision.get("status") in {"superseded", "revision_conflict", "unorderable", "not_checkable"}:
            comments.append({"severity": "major", "code": "REVISION_REVIEW",
                             "comment": f"Resolve document register finding: {revision['status']}.",
                             "source": "detect_previous_revisions"})
        for match in state.results.get("search_knowledge_base", {}).get("matches", []):
            for field in match.get("required_fields", []):
                if field not in fields and field not in checks["missing_fields"]:
                    comments.append({"severity": "major", "code": "REFERENCE_REQUIREMENT",
                                     "field": field, "comment": f"Provide {field.replace('_', ' ')} as requested in {match['id']}.",
                                     "source": match["id"], "evidence": match["text"]})
        if not comments:
            comments.append({"severity": "info", "code": "NO_METADATA_GAPS",
                             "comment": "No gaps found in the checks performed. Technical review is still required.",
                             "source": "check_completeness"})
        return {"comments": comments, "major_count": sum(c["severity"] == "major" for c in comments)}

    def recommend_next_action(self, state, **_):
        kind = state.results["classify_document"]["document_type"]
        checks = state.results["check_completeness"]
        revision = state.results.get("detect_previous_revisions", {}).get("status", "not_checked")
        comments = state.results.get("generate_review_comments", {})
        if kind == "unknown":
            action, reason = "manual_triage", "Document type is unknown or ambiguous."
        elif revision == "superseded":
            action, reason = "request_latest_revision", "A newer revision exists in the indexed register."
        elif revision in {"revision_conflict", "unorderable"}:
            action, reason = "resolve_revision_conflict", "The revision identity or sequence needs confirmation."
        elif not checks["complete"] or comments.get("major_count", 0):
            action, reason = "return_for_completion", "Required information is missing, invalid or conflicting."
        elif revision == "duplicate":
            action, reason = "record_duplicate", "The exact file already exists at the same registered revision."
        else:
            action, reason = "route_for_review", "Available metadata checks passed; assign a human reviewer."
        return {"action": action, "reason": reason, "human_review_required": True,
                "external_action_executed": False,
                "basis": list(state.results), "document_type": kind}

    def index_document(self, document):
        metadata = extract_fields(document)
        if metadata["conflicts"]:
            raise InputError("Resolve conflicting metadata before indexing.")
        if any(key not in metadata["fields"] for key in ("project", "document_number", "revision")):
            raise InputError("Indexing requires project, document number and revision.")
        return self.repository.index(document, metadata["fields"])


TOOL_SPECS = {
    "classify_document": {"description": "Identify the document type from its declared type or heading.", "requires": []},
    "extract_metadata": {"description": "Extract labelled metadata with source lines and conflicting values.", "requires": []},
    "search_knowledge_base": {"description": "Search the local training references for relevant requirements.", "requires": ["classify_document", "extract_metadata"]},
    "check_completeness": {"description": "Validate required metadata fields for the identified document type.", "requires": ["classify_document", "extract_metadata"]},
    "detect_previous_revisions": {"description": "Find older, newer, duplicate or conflicting registered revisions.", "requires": ["extract_metadata"]},
    "generate_summary": {"description": "Create a short extractive summary with source line evidence.", "requires": []},
    "generate_review_comments": {"description": "Create review comments from observed validation and reference findings.", "requires": ["check_completeness"]},
    "recommend_next_action": {"description": "Recommend a document-control action from observed findings.", "requires": ["classify_document", "extract_metadata", "check_completeness"]},
}
