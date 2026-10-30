from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.evaluation import evaluate

result = evaluate(ROOT / "data" / "evaluation.json", ROOT / "data" / "project.json")
target = ROOT / "outputs" / "evaluation_results.json"
target.parent.mkdir(exist_ok=True)
target.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
