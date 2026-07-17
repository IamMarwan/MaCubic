from app.schemas import Citation


def build_answer(question: str, retrieved_chunks: list[dict]) -> tuple[str, list[Citation]]:
    if not retrieved_chunks:
        return (
            "I could not find enough information in the uploaded documents to answer this question.",
            []
        )

    citations = [
        Citation(
            document=chunk["document"],
            chunk=chunk["chunk"]
        )
        for chunk in retrieved_chunks
    ]

    source_summary = "\n\n".join(
        f"[{chunk['document']} - Chunk {chunk['chunk']}]\n{chunk['content']}"
        for chunk in retrieved_chunks
    )

    answer = (
        "Based on the uploaded documents, the answer is supported by the following sources:\n\n"
        f"{source_summary}\n\n"
        "Summary answer:\n"
        f"The uploaded documents contain information related to: {question}. "
        "Please review the cited chunks above for the exact supporting details."
    )

    return answer, citations