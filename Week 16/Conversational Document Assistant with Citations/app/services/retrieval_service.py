from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import MIN_RELEVANCE_SCORE, TOP_K_RESULTS
from app.models import DocumentChunk


def retrieve_relevant_chunks(db: Session, question: str) -> list[dict]:
    chunks = db.query(DocumentChunk).all()

    if not chunks:
        return []

    chunk_texts = [chunk.content for chunk in chunks]
    documents = [chunk.document for chunk in chunks]

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2)
    )

    chunk_vectors = vectorizer.fit_transform(chunk_texts)
    question_vector = vectorizer.transform([question])

    scores = cosine_similarity(question_vector, chunk_vectors).flatten()

    ranked_results = sorted(
        zip(chunks, documents, scores),
        key=lambda item: item[2],
        reverse=True
    )

    results = []

    for chunk, document, score in ranked_results[:TOP_K_RESULTS]:
        if score >= MIN_RELEVANCE_SCORE:
            results.append(
                {
                    "document": document.filename,
                    "chunk": chunk.chunk_index,
                    "content": chunk.content,
                    "score": float(score),
                }
            )

    return results