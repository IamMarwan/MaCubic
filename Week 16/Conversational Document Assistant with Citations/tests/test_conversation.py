from app.services.answer_service import build_answer


def test_empty_answer():
    answer, citations = build_answer(
        "What is the project budget?",
        []
    )

    assert "could not find enough information" in answer.lower()
    assert citations == []


def test_citation_creation():
    chunks = [
        {
            "document": "project.txt",
            "chunk": 1,
            "content": "Project requirements",
            "score": 0.92,
        }
    ]

    answer, citations = build_answer(
        "What are the requirements?",
        chunks,
    )

    assert len(citations) == 1
    assert citations[0].document == "project.txt"