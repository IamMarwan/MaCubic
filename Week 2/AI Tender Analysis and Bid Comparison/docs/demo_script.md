# Five-minute Week 2 demonstration

## 0:00–0:40 — Introduce the workspace

Open `http://127.0.0.1:8000`. Explain that the Week 1 tender register now feeds a bidder comparison workspace with 30 tender requirement IDs and three synthetic bidders.

## 0:40–1:30 — Compare bidders

Show the 90 requirement-bid rows. Filter to each bidder, then to a category and a status. Turn on **Mandatory gaps only** and explain why missing evidence is kept separate from an explicit refusal.

## 1:30–2:20 — Open evidence and the tender source

Open a `met` row and show both the tender clause and bidder commitment with PDF page links. Explain that mandatory findings cannot be marked met without a bid passage.

## 2:20–3:10 — Surface deviations

Filter `partially met` and show the delivery-time deviation for Northstar Works and the alternative technical proposal for Cedar Build. Open Cedar's explicit exclusion for REQ-04. Show the contradiction flag on Summit Contracting's REQ-20 responses and the warranty gap on REQ-23.

## 3:10–4:00 — Clarifications and missing evidence

Download the clarification CSV. Point out that every question contains a bidder and requirement ID. Open a `not evidenced` row and show the list of bid documents searched, including the unrelated catalog that was not treated as proof.

## 4:00–5:00 — Evaluation and limits

Open `annotations/evaluation_report.md`. Show the 90-pair exact status agreement, per-status precision/recall/F1, confusion matrix, and ID-free paraphrase, contradiction, omission, and irrelevant-attachment checks. Finish by noting that the score is specific to synthetic fixtures and is not a real-bid accuracy guarantee. Confirm the separate Week 4 fixture was not used.
