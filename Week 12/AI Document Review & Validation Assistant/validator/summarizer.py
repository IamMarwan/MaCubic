import re
from collections import Counter
from typing import List

from validator.models import DocumentSummary


class DocumentSummarizer:
    def summarize(self, text: str, title: str = "Untitled Document") -> DocumentSummary:
        cleaned_text = self._clean_text(text)
        words = self._extract_words(cleaned_text)
        sentences = self._split_sentences(cleaned_text)

        keywords = self._extract_keywords(words)
        summary = self._build_summary(sentences, keywords)

        return DocumentSummary(
            title=title,
            summary=summary,
            keywords=keywords,
            word_count=len(words),
            character_count=len(cleaned_text)
        )

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _extract_words(self, text: str) -> List[str]:
        return re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())

    def _split_sentences(self, text: str) -> List[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text)

        return [
            sentence.strip()
            for sentence in sentences
            if len(sentence.strip()) > 20
        ]

    def _extract_keywords(self, words: List[str]) -> List[str]:
        stop_words = {
            "the", "and", "for", "with", "this", "that", "from",
            "will", "shall", "have", "has", "are", "was", "were",
            "document", "section", "page", "into", "been", "their",
            "there", "where", "which", "such", "each", "also"
        }

        filtered_words = [
            word for word in words
            if word not in stop_words
        ]

        counter = Counter(filtered_words)

        return [
            word for word, _ in counter.most_common(8)
        ]

    def _build_summary(self, sentences: List[str], keywords: List[str]) -> str:
        if not sentences:
            return "No readable summary could be generated because the document has limited text."

        scored_sentences = []

        for sentence in sentences:
            lower_sentence = sentence.lower()

            score = sum(
                1 for keyword in keywords
                if keyword in lower_sentence
            )

            scored_sentences.append((score, sentence))

        scored_sentences.sort(key=lambda item: item[0], reverse=True)

        selected_sentences = [
            sentence for _, sentence in scored_sentences[:3]
        ]

        return " ".join(selected_sentences)