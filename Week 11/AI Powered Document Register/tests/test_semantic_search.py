from app.semantic_search import SemanticSearchEngine


class MockDocument:
    def __init__(self, title, category, discipline, description, content):
        self.title = title
        self.category = category
        self.discipline = discipline
        self.description = description
        self.content = content


def test_semantic_search_returns_relevant_document():
    documents = [
        MockDocument(
            title="Foundation Drawing",
            category="Drawing",
            discipline="Structural",
            description="Foundation layout",
            content="Reinforced concrete foundations and structural supports."
        ),
        MockDocument(
            title="Electrical Layout",
            category="Drawing",
            discipline="MEP",
            description="Electrical layout",
            content="Lighting circuits and electrical distribution boards."
        )
    ]

    engine = SemanticSearchEngine()

    results = engine.search(
        query="concrete foundation structure",
        documents=documents
    )

    assert results[0][0].title == "Foundation Drawing"