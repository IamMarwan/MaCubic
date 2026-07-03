from typing import List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models import Document


class SemanticSearchEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words="english")

    def search(
        self,
        query: str,
        documents: List[Document],
        limit: int = 5
    ) -> List[Tuple[Document, float]]:

        if not documents:
            return []

        corpus = [
            f"{doc.title} {doc.category} {doc.discipline} "
            f"{doc.description or ''} {doc.content}"
            for doc in documents
        ]

        matrix = self.vectorizer.fit_transform(corpus)
        query_vector = self.vectorizer.transform([query])

        scores = cosine_similarity(query_vector, matrix).flatten()

        ranked_results = sorted(
            zip(documents, scores),
            key=lambda item: item[1],
            reverse=True
        )

        return ranked_results[:limit]