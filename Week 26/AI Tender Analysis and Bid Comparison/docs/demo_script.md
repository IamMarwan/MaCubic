# Five-minute demonstration script

## 0:00–0:40 — Show the product

Open the local register viewer at `http://127.0.0.1:8000`. Explain that the prototype stores a standalone synthetic tender register and provides source citations. Confirm that no external system or account is connected.

## 0:40–1:30 — Ingest the development package

Click **Load development fixture**. Point out the 30 development requirements, the BOQ workbook, three bid workbooks, and the amendment PDF included in `fixtures/development/`. Show the status counts.

## 1:30–2:20 — Inspect evidence

Search for `REQ-08`, click its source file, and show the PDF page text. Identify the page quotation attached to the row. Show that the amendment is revision 2 and retains a `SUPERSEDES` history entry. Inspect `REQ-03` or `REQ-21` to show an explicit conflict flag.

## 2:20–3:10 — Explain missing and optional values

Filter by `optional` or search a row with unknown fields. Explain that missing quantity, threshold, unit, or deadline values appear as `unknown` and are not inferred. Mention that bidder/BOQ workbooks are supplied as searchable spreadsheet fixtures with synthetic quantities, rates, and line totals.

## 3:10–4:10 — Export and idempotency

Download JSON and CSV from the toolbar or `/api/export.json` and `/api/export.csv`. Click **Load development fixture** again and point out that the register remains deduplicated by stable requirement ID.

## 4:10–5:00 — Benchmark and reserved package

Open `annotations/evaluation_report.md` and explain precision, recall, counts, and the fixed-format limitation. Show the separate `fixtures/week4_reserved/` package and its frozen reference manifest. State that it is reserved and is not used to tune the Week 26 development benchmark.
