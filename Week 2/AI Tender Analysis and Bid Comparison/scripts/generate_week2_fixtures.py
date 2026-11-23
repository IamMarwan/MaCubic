from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import fitz
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
DEV = ROOT / "fixtures" / "development"
BIDS = DEV / "bids"
ANN = ROOT / "annotations"
BIDDERS = ["Northstar Works", "Cedar Build", "Summit Contracting"]
OPTIONAL = {"REQ-05", "REQ-18", "REQ-26"}

DETAILS = {
    "REQ-01": ("Scope", "Complete civil, structural, and architectural works within the marked project boundary."),
    "REQ-02": ("Technical", "Demonstrate equipment efficiency of at least 90 percent under the stated operating test."),
    "REQ-03": ("Technical", "Maintain insurance coverage of at least AED 10 million throughout the contract."),
    "REQ-04": ("Commercial", "Disclose every qualification and exclusion that changes the offered scope or price."),
    "REQ-05": ("Submission", "Submit an optional sustainability improvement proposal with supporting evidence."),
    "REQ-06": ("Submission", "Provide the completed technical submission schedule in the required format."),
    "REQ-07": ("Technical", "Supply materials that meet the specified grade and approved product standards."),
    "REQ-08": ("Evaluation", "Meet the revised technical evaluation threshold of 75 points under amendment A-01."),
    "REQ-09": ("Deadline", "Deliver the complete bid package before the stated submission deadline."),
    "REQ-10": ("Commercial", "State the bid currency and confirm that all prices are firm for the offer period."),
    "REQ-11": ("Technical", "Identify any alternative technical solution and explain each departure from the tender design."),
    "REQ-12": ("Scope", "Include all listed installation, testing, and commissioning activities in the work scope."),
    "REQ-13": ("Technical", "Meet the specified noise limit at the project boundary during normal operation."),
    "REQ-14": ("Submission", "Provide valid manufacturer data sheets for each proposed major equipment item."),
    "REQ-15": ("Commercial", "Confirm the stated payment terms and identify any requested changes."),
    "REQ-16": ("Delivery", "Complete delivery within 90 calendar days after the notice to proceed."),
    "REQ-17": ("Technical", "Provide qualified personnel with the stated licenses and project experience."),
    "REQ-18": ("Evaluation", "Optional improvement: provide an extended energy performance guarantee."),
    "REQ-19": ("Scope", "Include protection, temporary works, and reinstatement for affected existing assets."),
    "REQ-20": ("Technical", "Declare all technical departures consistently across the offer and supporting schedules."),
    "REQ-21": ("Commercial", "Accept payment within 60 days as stated in the base tender clause."),
    "REQ-22": ("Submission", "Provide a project-specific quality plan and inspection schedule."),
    "REQ-23": ("Warranty", "State the warranty duration and every warranty exclusion for the supplied works."),
    "REQ-24": ("Technical", "Demonstrate that the proposed system integrates with the listed interfaces."),
    "REQ-25": ("Scope", "Remove and dispose of construction waste using the approved site procedures."),
    "REQ-26": ("Submission", "Optional improvement: provide a digital handover model in the requested format."),
    "REQ-27": ("Technical", "Meet the stated fire resistance rating for the identified assemblies."),
    "REQ-28": ("Deadline", "Complete commissioning and handover no later than the contractual completion date."),
    "REQ-29": ("Commercial", "Price all bill of quantities lines and identify assumptions affecting the total."),
    "REQ-30": ("Submission", "Submit a signed statement confirming the bid remains valid for 90 days."),
}


def make_pdf(path: Path, title: str, rows: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    page = landscape(letter)
    c = canvas.Canvas(str(path), pagesize=page)
    _, height = page
    for offset in range(0, len(rows) or 1, 8):
        c.setFont("Helvetica-Bold", 11)
        c.drawString(24, height - 34, title)
        c.setFont("Helvetica", 6.5)
        y = height - 60
        for row in rows[offset:offset + 8]:
            c.drawString(24, y, row[:2400])
            y -= 28
        c.setFont("Helvetica-Oblique", 7)
        c.drawString(24, 24, "Synthetic procurement training document")
        c.showPage()
    c.save()


def assignment(rid: str, bidder_index: int, optional: bool) -> str:
    # Deterministic hand-authored labels: coverage across every status, with targeted exceptions.
    special = {
        (0, "REQ-16"): "partially met",   # delivery deviation
        (1, "REQ-04"): "not met",         # explicit exclusion
        (1, "REQ-11"): "partially met",   # alternative proposal
        (2, "REQ-20"): "not evidenced",   # conflicting statements
        (2, "REQ-23"): "not evidenced",   # warranty evidence gap
    }
    if (bidder_index, rid) in special:
        return special[(bidder_index, rid)]
    number = int(rid.split("-")[1])
    code = (number + bidder_index * 2) % 17
    if code == 0:
        return "not applicable"
    if code in {1, 8, 15}:
        return "not evidenced"
    if code in {4, 12}:
        return "not met"
    if code in {2, 6, 10, 14}:
        return "partially met"
    # Optional requirements still have full responses in several cases, so status coverage is balanced.
    return "met"


def response_text(rid: str, status: str, bidder_index: int) -> str:
    category, description = DETAILS[rid]
    short = description.rstrip(".")
    if rid == "REQ-03" and status == "partially met":
        return "Our liability protection is limited to AED 5 million; an increased limit is subject to revised pricing."
    if rid == "REQ-04" and status == "not met":
        return "We exclude the listed commissioning support from our offer and will not provide it at the quoted price."
    if rid == "REQ-11" and status == "partially met":
        return "We propose an alternative control platform; compatibility evidence and approval are still required."
    if rid == "REQ-16" and status == "partially met":
        return "Our proposed shipment arrives in 120 days from the start notice, subject to the supplier slot."
    if rid == "REQ-20" and bidder_index == 2:
        return "The technical schedule confirms full compliance with every listed departure requirement."
    if rid == "REQ-23" and bidder_index == 2 and status == "not evidenced":
        return "Warranty duration and exclusions are not stated in the submitted bid package."
    if status == "met":
        variants = [
            f"We will fully comply: {short.lower()}. Supporting particulars are included in our {category.lower()} schedule.",
            f"Our signed offer confirms full compliance with this item: {short.lower()}; see the attached schedule for supporting particulars.",
            f"We accept the complete requirement to {short.lower()} and include the supporting details in our bid schedule.",
        ]
        return variants[(int(rid[-2:]) + bidder_index) % len(variants)]
    if status == "partially met":
        return f"We can address {short.lower()} in part; the stated limitation requires a clarification before award."
    if status == "not met":
        return f"We cannot meet {short.lower()} within this offer and have excluded the related work."
    if status == "not applicable":
        return f"Not applicable: this item falls outside our assigned lot, which covers only the north service zone; see our scope split." 
    return ""


def main() -> None:
    ANN.mkdir(parents=True, exist_ok=True)
    # Improve the inherited Week 1 reference descriptions while keeping every stable ID.
    ref_path = ANN / "development_reference.json"
    ref = json.loads(ref_path.read_text(encoding="utf-8"))
    week1 = ANN / "week1"
    week1.mkdir(exist_ok=True)
    if not (week1 / "development_reference.json").exists():
        shutil.copy2(ref_path, week1 / "development_reference.json")
    for report_name in ["evaluation_report.json", "evaluation_report.md"]:
        source = ANN / report_name
        if source.exists() and not (week1 / report_name).exists():
            shutil.copy2(source, week1 / report_name)
    for row in ref["requirements"]:
        category, description = DETAILS[row["id"]]
        row["category"] = category
        row["description"] = description
        row["source_file"] = "tender_requirements.pdf"
        row["source_page"] = ((int(row["id"].split("-")[1]) - 1) // 8) + 1
    ref_path.write_text(json.dumps(ref, indent=2), encoding="utf-8")
    # Rebuild the searchable requirement PDF so source quotations match the evolved register.
    req_lines = []
    for row in ref["requirements"]:
        req_lines.append(" | ".join([row["id"], row["category"], row["description"], row["status"],
                                      f"quantity={row['quantity']}", f"unit={row['unit']}",
                                      f"threshold={row['threshold']}", f"deadline={row['deadline']}",
                                      f"rev={row['rev']}"]))
    make_pdf(DEV / "tender_requirements.pdf", "TND-2026-041 · Tender Requirements · Revised W2 Fixture", req_lines)

    pairs = []
    per_bidder_files = {}
    for bidder_index, bidder in enumerate(BIDDERS):
        slug = bidder.lower().replace(" ", "_")
        folder = BIDS / slug
        folder.mkdir(parents=True, exist_ok=True)
        # Deliberately split and reorder bidder material across multiple source files.
        documents = {
            "technical_proposal.pdf": [],
            "commercial_schedule.pdf": [],
            "delivery_warranty_and_exclusions.pdf": [],
        }
        ordered = sorted(ref["requirements"], key=lambda row: ((int(row["id"][-2:]) * (bidder_index + 5)) % 31))
        for row in ordered:
            rid = row["id"]
            status = assignment(rid, bidder_index, row["status"] == "optional")
            text = response_text(rid, status, bidder_index)
            bucket = {"Technical": "technical_proposal.pdf", "Evaluation": "technical_proposal.pdf",
                      "Submission": "technical_proposal.pdf", "Scope": "technical_proposal.pdf",
                      "Commercial": "commercial_schedule.pdf", "Delivery": "delivery_warranty_and_exclusions.pdf",
                      "Warranty": "delivery_warranty_and_exclusions.pdf", "Deadline": "delivery_warranty_and_exclusions.pdf"}[row["category"]]
            if text:
                documents[bucket].append(f"EVIDENCE | {rid} | {text}")
            question = ""
            if status != "met":
                question = f"Please confirm the bidder's position and provide supporting evidence for {rid}."
            pair = {"pair_id": f"{slug}::{rid}", "requirement_id": rid, "bidder": bidder,
                    "gold_status": status, "rationale": f"Manual label: {status}; based on the submitted passage or documented absence.",
                    "unresolved_question": question, "optional": row["status"] == "optional"}
            pairs.append(pair)

        # Add a seeded second statement to expose a direct contradiction.
        if bidder_index == 2:
            documents["technical_proposal.pdf"].append(
                "EVIDENCE | REQ-20 | Our commercial qualifications exclude every technical departure and we will not supply omitted changes.")
        for filename, lines in documents.items():
            make_pdf(folder / filename, f"{bidder} · {filename.replace('_', ' ').replace('.pdf', '')}", lines)
        # A separate irrelevant catalog tests that irrelevant attachments do not become evidence.
        irrelevant = folder / "general_product_catalog.pdf"
        make_pdf(irrelevant, f"{bidder} · General Product Catalog", [
            "General product information: standard color options, catalog dimensions, and stock packaging.",
            "No project requirement ID, project commitment, delivery term, warranty term, or tender response is stated."])
        per_bidder_files[bidder] = [f"bids/{slug}/{name}" for name in documents] + [f"bids/{slug}/general_product_catalog.pdf"]

    # Bind source references to their PDF page and quotation after the generated PDFs exist.
    labels_path = ANN / "labeled_90_pairs.csv"
    with labels_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["pair_id", "bidder", "requirement_id", "gold_status", "rationale", "unresolved_question", "optional"])
        writer.writeheader()
        writer.writerows(pairs)
    (ANN / "bid_search_manifest.json").write_text(json.dumps(per_bidder_files, indent=2), encoding="utf-8")
    # Decision cases exercise ID-free paraphrase matching, conflict handling, omission, and irrelevant evidence.
    tests = [
        {"case": "paraphrase_delivery", "text": "Shipment and arrival will occur within ninety calendar days of the start authorization.", "expected_requirement_id": "REQ-16"},
        {"case": "paraphrase_warranty", "text": "The guarantee period and its carve-outs for supplied work are provided in our schedule.", "expected_requirement_id": "REQ-23"},
        {"case": "contradiction", "text": "REQ-20 has one affirmative compliance statement and a second statement excluding the same technical departures.", "expected_status": "not evidenced"},
        {"case": "omitted_answer", "text": "No passage mapped to REQ-23 across all searched bid files.", "expected_status": "not evidenced"},
        {"case": "irrelevant_attachment", "text": "A general catalog with no tender ID or project commitment is not supporting evidence.", "expected_status": "not evidenced"},
    ]
    (ANN / "adversarial_cases.json").write_text(json.dumps(tests, indent=2), encoding="utf-8")
    print(f"Generated {len(pairs)} manually labeled bidder-requirement pairs and bidder source PDFs.")


if __name__ == "__main__":
    main()
