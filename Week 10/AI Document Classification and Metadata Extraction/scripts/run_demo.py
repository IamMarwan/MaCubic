import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))


from app.classifier import classify_document
from app.extractor import extract_metadata
from app.file_parser import extract_text
from scripts.generate_sample_dataset import main as generate_dataset


def run_demo():

    dataset_dir = BASE_DIR / "generated_dataset" / "docx"

    if not dataset_dir.exists() or not list(dataset_dir.glob("*.docx")):
        generate_dataset()

    files = sorted(dataset_dir.glob("*.docx"))

    print("AI Document Classification & Metadata Extraction Demo")
    print("=" * 60)

    for file in files[:50]:

        text = extract_text(str(file))

        document_type, confidence_score = classify_document(text)
        metadata = extract_metadata(text)

        print(f"File: {file.name}")
        print(f"Classification: {document_type}")
        print(f"Confidence Score: {confidence_score}")
        print(f"Document Title: {metadata.get('document_title')}")
        print(f"Project Name: {metadata.get('project_name')}")
        print(f"Contractor: {metadata.get('contractor')}")
        print(f"Consultant: {metadata.get('consultant')}")
        print(f"Submission Date: {metadata.get('submission_date')}")
        print(f"Discipline: {metadata.get('discipline')}")
        print("-" * 60)


if __name__ == "__main__":
    run_demo()