from pathlib import Path
import yaml


def load_rules(path):
    rule_path = Path(path)

    with rule_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    if "document_types" not in data:
        raise ValueError("Rules file must contain a document_types section.")

    return data