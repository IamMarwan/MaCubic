"""Regenerate the checked-in sample inputs and expected scenario manifest."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import ROOT
from scripts.scenarios import BASE_DRAWING, KNOWLEDGE_BASE, SCENARIOS


def main():
    folder = ROOT / "data" / "samples"
    folder.mkdir(parents=True, exist_ok=True)
    for scenario in SCENARIOS:
        (folder / f"{scenario['id']}.txt").write_text(scenario["text"], encoding="utf-8")
    (ROOT / "data" / "previous_drawing_rev01.txt").write_text(BASE_DRAWING, encoding="utf-8")
    (ROOT / "data" / "knowledge_base.json").write_text(json.dumps(KNOWLEDGE_BASE, indent=2), encoding="utf-8")
    manifest = [{key: value for key, value in s.items() if key != "text"} for s in SCENARIOS]
    (ROOT / "data" / "scenarios.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Generated {len(SCENARIOS)} fictional sample documents, prior revision, references and scenario manifest.")


if __name__ == "__main__":
    main()
