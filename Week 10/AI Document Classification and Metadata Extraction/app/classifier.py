from app.config import DOCUMENT_TYPES


def classify_document(text: str):
    text = text.lower()

    scores = {}

    for doc_type, keywords in DOCUMENT_TYPES.items():
        score = 0

        for keyword in keywords:
            if keyword.lower() in text:
                score += 1

        scores[doc_type] = score

    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    total_score = sum(scores.values())

    if best_score == 0:
        return "Unknown", 0.0

    confidence = best_score / total_score

    return best_type, round(confidence, 2)