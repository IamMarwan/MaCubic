from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any


TODAY = date(2026, 10, 30)


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9-]+", text.lower())
    normalized = set(words)
    for word in words:
        if len(word) > 4 and word.endswith("ies"):
            normalized.add(word[:-3] + "y")
        elif len(word) > 3 and word.endswith("s"):
            normalized.add(word[:-1])
    return normalized


class ProjectAgent:
    """Deterministic, inspectable orchestration over a simulated document collection."""

    def __init__(self, dataset_path: Path):
        self.dataset_path = Path(dataset_path)
        self.project = json.loads(self.dataset_path.read_text(encoding="utf-8"))
        self.docs = {d["id"]: d for d in self.project["documents"]}
        self.trace: list[dict[str, Any]] = []

    def _log(self, step: str, tool: str, inputs: dict[str, Any], result: Any) -> None:
        self.trace.append({"sequence": len(self.trace) + 1, "step": step, "tool": tool,
                           "inputs": inputs, "result_summary": result})

    def understand(self, request: str) -> dict[str, Any]:
        terms = _tokens(request)
        focus = []
        mapping = {
            "risks": ("risk", "delay", "schedule", "nonconformance"),
            "actions": ("action", "overdue", "outstanding", "minutes"),
            "commercial": ("contract", "commercial", "payment", "variation", "claim"),
            "technical": ("rfi", "submittal", "inspection", "specification"),
            "conflicts": ("conflict", "contradict", "disagree", "inconsistent"),
        }
        for label, synonyms in mapping.items():
            if any(t in terms for t in _tokens(" ".join(synonyms))):
                focus.append(label)
        if "major" in terms or "all" in terms or {"outstanding", "issues"}.issubset(terms):
            focus = list(mapping)
        if not focus:
            focus = list(mapping)
        plan = [
            "Search project records for issue, risk, action, and status evidence.",
            "Read high-relevance records and follow their document relationships.",
            "Extract dated obligations, open items, risks, and conflicting statements.",
            "Check that each finding has source evidence; label fact, inference, and recommendation.",
            "Produce a management report and preserve the full execution trace.",
        ]
        result = {"project": self.project["project_name"], "focus": focus, "plan": plan}
        self._log("understand_request", "request_interpreter", {"request": request}, result)
        return result

    def search_documents(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        stopwords = {"the", "and", "for", "with", "what", "this", "that", "from", "into", "check", "status", "list", "find", "identify", "analyze", "analyse", "project"}
        terms = {t for t in re.findall(r"[a-z0-9-]+", query.lower()) if len(t) > 2 and t not in stopwords}
        ranked = []
        for doc in self.project["documents"]:
            haystack = " ".join([doc["title"], doc["type"], doc["status"], doc["text"]]).lower()
            overlap = sum(1 for term in terms if term in haystack)
            if overlap:
                ranked.append((overlap, doc["id"], doc))
        ranked.sort(key=lambda x: (-x[0], x[1]))
        results = [d for _, _, d in ranked[:limit]]
        self._log("search_project", "search_documents", {"query": query, "limit": limit},
                  {"count": len(results), "document_ids": [d["id"] for d in results]})
        return results

    def read_document(self, document_id: str) -> dict[str, Any] | None:
        doc = self.docs.get(document_id)
        summary = None if doc is None else {"document_id": document_id, "title": doc["title"],
                                            "signal_count": len(doc.get("signals", []))}
        self._log("gather_evidence", "read_document", {"document_id": document_id}, summary)
        return doc

    def follow_relationships(self, document_ids: list[str]) -> list[str]:
        found = set()
        for document_id in document_ids:
            doc = self.docs.get(document_id)
            if doc:
                found.update(doc.get("related_documents", []))
        found.difference_update(document_ids)
        ids = sorted(found)
        self._log("follow_relationships", "related_documents", {"document_ids": document_ids}, ids)
        return ids

    def assess_findings(self, request: str) -> list[dict[str, Any]]:
        initial = self.search_documents(request, limit=12)
        category_terms = {
            "risk": ("risk", "nonconformance", "ncr", "inspection", "compliance"),
            "action": ("action", "overdue", "minutes", "outstanding"),
            "delay": ("delay", "schedule", "commissioning", "milestone"),
            "commercial": ("commercial", "contract", "variation", "claim", "payment", "notice"),
            "technical": ("rfi", "submittal", "technical", "unresolved"),
            "conflict": ("conflict", "contradict", "access", "disagree", "inconsistent"),
        }
        request_terms = _tokens(request)
        referenced_ids = [x.lower() for x in re.findall(r"\b(?:rfi|submittal|sub|ncr|action|a|v)-?\d+\b", request, re.I)]
        selected_categories = {cat for cat, terms in category_terms.items()
                               if any(term in request_terms for term in terms)}
        if any(term in request_terms for term in ("all", "overall", "major")):
            selected_categories = set(category_terms)
        if not selected_categories:
            selected_categories = set(category_terms)
        # For a request spanning several areas, run a focused retrieval query per area.
        # This keeps broad management reviews from depending on one top-k ranking.
        focused_docs = list(initial)
        for category in sorted(selected_categories):
            q = " ".join(category_terms[category])
            focused_docs.extend(self.search_documents(q, limit=8))
        initial_ids = list(dict.fromkeys(d["id"] for d in focused_docs))
        related_ids = self.follow_relationships(initial_ids)
        selected_ids = list(dict.fromkeys(initial_ids + related_ids))
        candidates: dict[str, dict[str, Any]] = {}
        for doc_id in selected_ids:
            doc = self.read_document(doc_id)
            if not doc:
                continue
            # Linked records are read and traced to establish relationships; findings are
            # raised only from documents directly retrieved for the user's request.
            if doc_id not in initial_ids:
                continue
            for signal in doc.get("signals", []):
                signal_text = " ".join((signal.get("finding_id", ""), signal.get("title", ""), signal.get("fact", ""))).lower().replace("-", "")
                if referenced_ids and not any(ref.replace("-", "") in signal_text for ref in referenced_ids):
                    continue
                if signal.get("category") in selected_categories and signal.get("status") in {"open", "overdue", "at_risk", "disputed", "conflict", "pending"}:
                    candidates.setdefault(signal["finding_id"], {**signal, "sources": []})["sources"].append(doc)
        findings = []
        for finding_id, item in candidates.items():
            sources = []
            for doc in item["sources"]:
                line = item.get("evidence_line", 1)
                lines = doc["text"].splitlines()
                quote = lines[line - 1] if 0 < line <= len(lines) else doc["text"][:180]
                sources.append({"document_id": doc["id"], "title": doc["title"],
                                "line": line, "quote": quote})
            findings.append({"id": finding_id, "category": item["category"], "title": item["title"],
                             "status": item["status"], "severity": item["severity"],
                             "fact": item["fact"], "inference": item.get("inference"),
                             "recommendation": item.get("recommendation"), "sources": sources,
                             "evidence_sufficient": bool(sources)})
        findings.sort(key=lambda f: ({"critical": 0, "high": 1, "medium": 2, "low": 3}.get(f["severity"], 4), f["id"]))
        self._log("assess_evidence", "evidence_assessor", {"documents_considered": len(selected_ids)},
                  {"finding_count": len(findings), "finding_ids": [f["id"] for f in findings],
                   "unsupported_findings": [f["id"] for f in findings if not f["evidence_sufficient"]]})
        return findings

    def investigate(self, request: str) -> dict[str, Any]:
        self.trace = []
        context = self.understand(request)
        findings = self.assess_findings(request)
        report = self._render_report(context, findings)
        self._log("produce_report", "report_builder", {"finding_count": len(findings)},
                  {"citation_count": sum(len(f["sources"]) for f in findings), "report_status": "complete"})
        return {"request": request, "project": self.project["project_name"],
                "as_of": self.project["as_of"], "focus": context["focus"],
                "findings": findings, "report_markdown": report, "trace": self.trace}

    def _render_report(self, context: dict[str, Any], findings: list[dict[str, Any]]) -> str:
        high = [f for f in findings if f["severity"] in {"critical", "high"}]
        lines = [f"# Project Intelligence Report — {self.project['project_name']}", "",
                 f"**As of:** {self.project['as_of']}  ", f"**Request focus:** {', '.join(context['focus'])}", "",
                 "## Executive summary", "",
                f"The investigation reviewed linked project records and identified {len(findings)} evidence-backed open items, including {len(high)} high or critical findings. The results below are limited to the supplied simulated records; they are not a contractual determination or an approved schedule forecast.", ""]
        groups = [
            ("Major risks", lambda f: f["category"] == "risk"),
            ("Outstanding actions", lambda f: f["category"] == "action"),
            ("Potential delays", lambda f: f["category"] == "delay"),
            ("Contractual and commercial issues", lambda f: f["category"] == "commercial"),
            ("Unresolved RFIs and submittals", lambda f: f["category"] == "technical"),
            ("Conflicting information", lambda f: f["category"] == "conflict"),
        ]
        for heading, predicate in groups:
            items = [f for f in findings if predicate(f)]
            lines.extend([f"## {heading}", ""])
            if not items:
                lines.extend(["No qualifying item was identified in the reviewed records.", ""])
                continue
            for item in items:
                lines.extend([f"### {item['title']} — {item['severity'].upper()}", "",
                              f"**Fact:** {item['fact']}"])
                if item.get("inference"):
                    lines.append(f"**Inference:** {item['inference']}")
                if item.get("recommendation"):
                    lines.append(f"**Recommendation:** {item['recommendation']}")
                citations = "; ".join(f"[{s['document_id']}, line {s['line']}] {s['title']} — “{s['quote']}”" for s in item["sources"])
                lines.extend([f"**Evidence:** {citations}" if citations else "**Evidence:** Insufficient; excluded from conclusions.", ""])
        lines.extend(["## Evidence limitations", "",
                      "This is a deterministic demonstration over a fictional dataset. Dates and statuses reflect the dataset's stated as-of date. Conflicting sources are preserved for review; the agent does not decide which party is correct. Recommendations are review prompts, not instructions to change records or take external action.", ""])
        return "\n".join(lines)
