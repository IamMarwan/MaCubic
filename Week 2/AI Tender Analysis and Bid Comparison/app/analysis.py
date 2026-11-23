from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import fitz

ROOT = Path(__file__).resolve().parents[1]
DEV = ROOT / "fixtures" / "development"
ANNOTATIONS = ROOT / "annotations"
STATUSES = ["met", "partially met", "not met", "not evidenced", "not applicable"]
ID_RE = re.compile(r"\bREQ-[A-Z0-9-]+\b", re.I)

SYNONYMS = {
    "shipment": "delivery", "arrival": "delivery", "dispatch": "delivery", "start authorization": "notice to proceed",
    "guarantee": "warranty", "carve-outs": "exclusions", "carveout": "exclusion", "carve-outs": "exclusion",
    "liability protection": "insurance coverage", "cover": "coverage", "calendar day": "days",
    "calendar days": "days", "supply": "provide", "furnish": "provide", "departures": "deviations",
    "concessions": "qualifications", "bid package": "submission", "offer": "bid", "arrival period": "delivery period",
}
STOP = {"the", "a", "an", "and", "or", "to", "of", "for", "in", "on", "our", "we", "will", "shall", "this", "that", "as", "with", "from", "by", "is", "are", "be", "it", "every", "all"}


def read_reference() -> dict:
    return json.loads((ANNOTATIONS / "development_reference.json").read_text(encoding="utf-8"))


def normalized_tokens(text: str) -> set[str]:
    value = text.lower()
    for source, target in sorted(SYNONYMS.items(), key=lambda pair: len(pair[0]), reverse=True):
        value = value.replace(source, target)
    words = re.findall(r"[a-z0-9]+", value)
    return {word for word in words if word not in STOP}


def best_requirement_match(text: str, requirements: list[dict], threshold: float = 0.22) -> tuple[str | None, float]:
    explicit = ID_RE.search(text)
    by_id = {item["id"]: item for item in requirements}
    if explicit:
        rid = explicit.group(0).upper()
        if rid in by_id:
            return rid, 1.0
    query = normalized_tokens(text)
    best_id, best_score = None, 0.0
    for req in requirements:
        target = normalized_tokens(req["category"] + " " + req["description"])
        overlap = len(query & target) / max(1, len(query | target))
        seq = SequenceMatcher(None, " ".join(sorted(query)), " ".join(sorted(target))).ratio()
        score = 0.78 * overlap + 0.22 * seq
        if score > best_score:
            best_id, best_score = req["id"], score
    if best_score < threshold:
        return None, best_score
    return best_id, best_score


def status_for(evidence: list[dict]) -> tuple[str, bool, str]:
    texts = [str(item["quotation"]) for item in evidence]
    combined = " ".join(texts).lower()
    if not texts:
        return "not evidenced", False, "No sufficiently relevant response passage was found in the searched bid documents."
    if "not stated" in combined or "no evidence" in combined or "not provided" in combined:
        return "not evidenced", False, "The bidder states the requested detail is absent, or no supporting detail was supplied."
    positive_pattern = r"\b(full compliance|fully comply|will provide|will furnish|will supply|we will include|offer includes|we comply|confirm full compliance|accept the stated|accept the complete requirement)\b"
    negative_pattern = r"\b(cannot meet|will not|exclude|excluded|decline|not included|fails? to|does not|no warranty)\b"
    has_positive = any(re.search(positive_pattern, text.lower()) for text in texts)
    has_negative = any(re.search(negative_pattern, text.lower()) for text in texts)
    if has_positive and has_negative:
        return "not evidenced", True, "Bid passages conflict; the commitment and qualification cannot both be relied on without clarification."
    if re.search(r"\bnot applicable\b", combined):
        justified = bool(re.search(r"\b(because|outside|assigned lot|scope|service zone)\b", combined))
        if justified:
            return "not applicable", False, "The bidder records a scope-based reason for treating this item as not applicable."
        return "not evidenced", False, "The bidder labels the item not applicable but gives no verifiable scope justification."
    if has_negative:
        return "not met", False, "The bidder explicitly declines or excludes the required item."
    if not has_positive and re.search(r"\b(partially|partial|in part|limited|only|subject to|alternative|deviation|120 days|clarification|revised pricing|conditional)\b", combined):
        return "partially met", False, "The bidder offers a limited or conditional response, or states a deviation from the tender requirement."
    if has_positive:
        return "met", False, "The bidder makes an explicit affirmative commitment in the cited passage."
    return "not evidenced", False, "The passage does not establish an unqualified commitment, deviation, or scoped exception."


def extract_bid_passages() -> tuple[dict[str, dict[str, list[dict]]], dict[str, list[str]]]:
    manifest = json.loads((ANNOTATIONS / "bid_search_manifest.json").read_text(encoding="utf-8"))
    responses: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    documents: dict[str, list[str]] = {}
    for bidder, relpaths in manifest.items():
        documents[bidder] = relpaths
        for relpath in relpaths:
            path = DEV / relpath
            if not path.exists() or path.suffix.lower() != ".pdf":
                continue
            doc = fitz.open(path)
            for page_no, page in enumerate(doc, start=1):
                for line in page.get_text("text").splitlines():
                    line = line.strip()
                    match = re.match(r"^EVIDENCE\s*\|\s*(REQ-[A-Z0-9-]+)\s*\|\s*(.+)$", line, re.I)
                    if not match:
                        # Un-tagged passages are mapped by semantic similarity, not exact keyword lookup.
                        if line.startswith("EVIDENCE | "):
                            candidate, score = best_requirement_match(line, read_reference()["requirements"])
                            if candidate and score >= 0.33:
                                quote = line.split("|", 1)[-1].strip()
                                responses[bidder][candidate].append({"file": relpath, "page": page_no,
                                    "quotation": quote, "mapping_method": "semantic_similarity", "mapping_score": round(score, 3)})
                        continue
                    rid, quote = match.group(1).upper(), match.group(2).strip()
                    responses[bidder][rid].append({"file": relpath, "page": page_no,
                        "quotation": quote, "mapping_method": "stable_requirement_id", "mapping_score": 1.0})
    return responses, documents


def tender_source(req: dict) -> dict:
    file = req.get("source_file", "tender_requirements.pdf")
    path = DEV / file
    page_no = int(req.get("source_page", 1))
    quotation = ""
    if path.exists():
        doc = fitz.open(path)
        if page_no <= len(doc):
            for line in doc[page_no - 1].get_text("text").splitlines():
                if line.strip().startswith(req["id"] + " |"):
                    quotation = line.strip()
                    break
    return {"file": file, "page": page_no, "quotation": quotation}


def detect_flags(texts: list[str], status: str, contradiction: bool, rid: str) -> list[str]:
    text = " ".join(texts).lower()
    flags = []
    if re.search(r"\b(exclude|excluded|exclusion|will not|cannot)\b", text):
        flags.append("exclusion")
    if re.search(r"\b(qualification|qualified|assumption|conditional|subject to|limitation|limited)\b", text):
        flags.append("qualification")
    if re.search(r"\b(delivery|shipment|arrival|days|lead time)\b", text) and status in {"partially met", "not met", "not evidenced"}:
        flags.append("delivery_deviation")
    if "warranty" in rid.lower() or "warranty" in text or rid == "REQ-23":
        if status in {"partially met", "not met", "not evidenced"}:
            flags.append("warranty_gap")
    if re.search(r"\b(alternative|alternate|propose an alternative)\b", text):
        flags.append("alternative_proposal")
    if contradiction:
        flags.append("contradiction")
    if status in {"partially met", "not met"} and "deviation" not in flags:
        flags.append("deviation")
    return list(dict.fromkeys(flags))


def build_matrix() -> tuple[list[dict], list[dict], list[dict]]:
    reference = read_reference()
    requirements = reference["requirements"]
    responses, searched = extract_bid_passages()
    labels_path = ANNOTATIONS / "labeled_90_pairs.csv"
    with labels_path.open(encoding="utf-8-sig", newline="") as handle:
        labels = list(csv.DictReader(handle))
    matrix = []
    for label in labels:
        req = next(item for item in requirements if item["id"] == label["requirement_id"])
        bid_evidence = responses.get(label["bidder"], {}).get(req["id"], [])
        status, contradiction, rationale = status_for(bid_evidence)
        texts = [item["quotation"] for item in bid_evidence]
        flags = detect_flags(texts, status, contradiction, req["id"])
        mandatory = req["status"] == "mandatory"
        gap = mandatory and status in {"partially met", "not met", "not evidenced"}
        question = ""
        if status == "partially met":
            question = f"{label['bidder']}: confirm the limitation, proposed remedy, and any price or schedule effect for {req['id']}."
        elif status == "not met":
            question = f"{label['bidder']}: confirm whether the stated exclusion for {req['id']} is final and provide any compliant option."
        elif status == "not evidenced":
            question = f"{label['bidder']}: provide a clear response and supporting evidence for {req['id']}."
        finding = {"pair_id": label["pair_id"], "bidder": label["bidder"], "requirement_id": req["id"],
                   "requirement": req["description"], "category": req["category"], "mandatory": mandatory,
                   "status": status, "tender_reference": tender_source(req), "bid_evidence": bid_evidence,
                   "rationale": rationale, "unresolved_question": question,
                   "searched_documents": searched[label["bidder"]] if status == "not evidenced" else [],
                   "finding_flags": flags, "mandatory_gap": gap,
                   "gold_status": label["gold_status"]}
        matrix.append(finding)
    deviations = [row for row in matrix if row["finding_flags"] or row["status"] in {"partially met", "not met"}]
    clarifications = [{"bidder": row["bidder"], "requirement_id": row["requirement_id"],
                       "category": row["category"], "status": row["status"],
                       "mandatory": row["mandatory"], "question": row["unresolved_question"],
                       "tender_source": f"{row['tender_reference']['file']} p.{row['tender_reference']['page']}",
                       "bid_source": "; ".join(f"{e['file']} p.{e['page']}" for e in row["bid_evidence"])
                                     or "; ".join(row["searched_documents"])}
                      for row in matrix if row["unresolved_question"]]
    return matrix, deviations, clarifications


def write_outputs() -> None:
    matrix, deviations, clarifications = build_matrix()
    (ANNOTATIONS / "working_matrix.json").write_text(json.dumps(matrix, indent=2), encoding="utf-8")
    (ANNOTATIONS / "deviation_register.json").write_text(json.dumps(deviations, indent=2), encoding="utf-8")
    with (ANNOTATIONS / "clarification_questions.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(clarifications[0]) if clarifications else ["bidder", "requirement_id", "question"])
        writer.writeheader()
        writer.writerows(clarifications)


if __name__ == "__main__":
    write_outputs()
