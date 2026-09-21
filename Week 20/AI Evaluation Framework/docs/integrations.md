# Integrating models, prompts, embeddings and previous projects

## Export evaluation inputs without gold answers

```powershell
python run.py export-inputs --output outputs/public_inputs.json
```

The export includes corpus text, a corpus hash, a full benchmark identity hash, and 70 test task inputs. It excludes facts/expected answers. The hash authenticates identity, not correctness. Use the same exported inputs for each external model or previous-week project adapter. Responses must be converted to the explicit structured prediction contract in `evalkit/providers.py`.

## Import predictions from an existing API or agent

Create a JSON file at `outputs/external_predictions.json`:

```json
{
  "benchmark_hash": "COPY_FROM_PUBLIC_INPUTS",
  "model": "actual-model-or-agent-version",
  "records": [
    {
      "case_id": "P2-DRW-02-status",
      "retrieved_ids": ["P2-DRW-02"],
      "prediction": {
        "claims": [{
          "doc_id": "P2-DRW-02",
          "field": "status",
          "value": "Revise and resubmit",
          "citations": [{"doc_id": "P2-DRW-02", "quote": "Review status: Revise and resubmit"}]
        }],
        "metadata": {"project": null, "document_no": null, "revision": null, "issue_date": null, "status": null, "reviewer": null, "due_date": null},
        "label": null,
        "abstain": false
      },
      "latency_ms": null,
      "usage": {"input_tokens": null, "output_tokens": null, "cached_input_tokens": null, "source": "external_reported"}
    }
  ]
}
```

This is a schema example with a dataset-supported claim, **not fabricated evidence of an external model run**. Supply actual predictions for every selected case. Missing cases become recorded execution failures. Record original end-to-end latency and actual token counts when available; null means unknown. Do not time JSON replay and call it model latency. Provide the actual ranked document IDs, not gold relevant IDs.

Create `configs/external.json`:

```json
{
  "id": "external_agent_v1",
  "provider": "replay",
  "retrieval": "bm25",
  "top_k": 3,
  "predictions_file": "outputs/external_predictions.json"
}
```

Here retrieval identifies the declared external strategy; actual ranked IDs come from the imported records. The runner does not recompute their external retrieval. Add the same pricing fields used by the LLM configurations if counts and the applicable prices are available.

```powershell
python run.py run --config configs/external.json
python run.py report
```

Imported measurements are labeled `imported_unverified`. Compare two such runs with each other, preserving benchmark and code identities. The system does not silently treat imported evidence as freshly measured live API calls.

## Compare embedding models

Run the same exported corpus and question text through embedding model A and model B. Save one vector bundle for each, with all vectors from the same model/dimension within a bundle:

```json
{
  "model": "actual-embedding-model-version",
  "dimensions": 3,
  "corpus_hash": "COPY_FROM_PUBLIC_INPUTS",
  "build_notes": "Record actual embedding latency, token usage and cost here or in a separate measured report.",
  "documents": {
    "P1-DRW-02": [0.1, 0.2, 0.3]
  },
  "queries": {
    "P2-DRW-02-status": {
      "question_hash": "HASH_OF_EXACT_QUESTION",
      "vector": [0.2, 0.1, 0.4]
    }
  }
}
```

The numbers above illustrate schema only; this intentionally incomplete example cannot pass validation. Include all corpus IDs and every QA query in the chosen split. The hash function is `evalkit.common.digest`, which hashes canonical JSON, not raw file bytes. Produce the question hash with `digest(question_string)`. `public_inputs.json` supplies the corpus hash. Vectors must have matching positive dimensions, finite numeric entries, and nonzero norm. Corpus/query hash mismatches fail explicitly.

Copy `configs/candidate.json` to `configs/embedding_a.json`, change its ID to `embedding_a`, set `retrieval` to `vectors`, and add `vectors_file: "outputs/embedding_a.json"`. Create B the same way. Hold the classifier, extraction policy, case sample and k fixed.

```powershell
python run.py run --config configs/embedding_a.json
python run.py run --config configs/embedding_b.json
python run.py report
```

Compare recall@k, MRR and nDCG using the same split and k. Query/document embedding generation is outside these runs; compare its measured cost and latency separately. No neural embedding model was downloaded or run for the included evidence.

## Adapter boundaries

- Built-in corpus ingestion is UTF-8 text in JSON. Convert PDF/DOCX input with the earlier ingestion pipeline and preserve source IDs before evaluation. OCR/file-format parsing accuracy is outside this benchmark.
- The adapter does not automatically import your Week 19 project. It accepts normalized predictions from that project after you map its output to this contract.
- The built-in OpenAI adapter receives retrieved source text only. It uses provider-reported usage and returns no extra free-form answer paragraph.
- Credentials are read from the process environment. Model names, prompt content, prices and response IDs are recorded; API keys are not.
- Use synthetic or authorized documents for external model calls. The included dataset is fictional.
