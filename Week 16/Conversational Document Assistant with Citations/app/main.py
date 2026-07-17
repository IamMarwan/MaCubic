from fastapi import Depends, FastAPI, File, UploadFile
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.schemas import QuestionRequest, QuestionResponse, UploadDocumentResponse
from app.services.answer_service import build_answer
from app.services.conversation_service import (
    add_message,
    get_or_create_conversation,
)
from app.services.document_service import save_document
from app.services.retrieval_service import retrieve_relevant_chunks

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Conversational Document Assistant with Citations",
    description="Week 16 project: conversational API for document questions with citations.",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "Conversational Document Assistant with Citations is running."
    }


@app.post("/documents/upload", response_model=UploadDocumentResponse)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    document = save_document(db, file)

    return UploadDocumentResponse(
        document_id=document.id,
        filename=document.filename,
    )


@app.post("/chat/ask", response_model=QuestionResponse)
def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db),
):
    conversation = get_or_create_conversation(
        db=db,
        conversation_id=request.conversation_id,
    )

    add_message(
        db=db,
        conversation_id=conversation.id,
        role="user",
        message=request.question,
    )

    retrieved_chunks = retrieve_relevant_chunks(
        db=db,
        question=request.question,
    )

    answer, citations = build_answer(
        question=request.question,
        retrieved_chunks=retrieved_chunks,
    )

    add_message(
        db=db,
        conversation_id=conversation.id,
        role="assistant",
        message=answer,
    )

    return QuestionResponse(
        answer=answer,
        conversation_id=conversation.id,
        citations=citations,
    )