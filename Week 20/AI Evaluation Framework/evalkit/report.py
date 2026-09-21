"""Self-contained offline comparison dashboard and CSV export."""
import csv
import json
from pathlib import Path
from .common import ROOT,read_json

def generate_report(output):
    output=Path(output)
    runs=[read_json(p) for p in sorted((output/'runs').glob('*.json'))]
    if not runs: raise ValueError('No completed result files; run an evaluation first')
    template=(ROOT/'web'/'report.html').read_text(encoding='utf-8')
    payload=json.dumps(runs,ensure_ascii=False,allow_nan=False).replace('<','\\u003c')
    # JSON escape must contain one backslash in the HTML payload.
    payload=payload.replace('\\\\u003c','\\u003c')
    path=output/'comparison.html'
    path.write_text(template.replace('__EVAL_DATA__',payload),encoding='utf-8')
    keys=['run_id','created_at','config','evidence_type','split','cases','errors','task_success','answer_correctness',
          'retrieval_recall','retrieval_precision','mrr','ndcg','citation_accuracy','citation_coverage','gold_citation_recall',
          'hallucination_rate','metadata_micro_accuracy','metadata_f1','classification_accuracy','classification_macro_f1',
          'latency_mean_ms','latency_p95_ms','input_tokens','output_tokens','estimated_cost_usd','successful_cases_per_usd']
    with (output/'summary.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader()
        for run in runs:
            m=run['manifest'];row={k:run['summary'].get(k) for k in keys}
            row.update(run_id=m['run_id'],created_at=m['created_at'],config=m['config']['id'],evidence_type=m['evidence_type'],split=m['split'])
            writer.writerow(row)
    return path
