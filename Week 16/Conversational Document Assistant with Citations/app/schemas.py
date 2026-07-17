from pydantic import BaseModel


class UploadDocumentResponse(BaseModel):
    document_id: int
    filename: str


class QuestionRequest(BaseModel):
    question: str
    conversation_id: int | None = None


class Citation(BaseModel):
    document: str
    chunk: int


class QuestionResponse(BaseModel):
    answer: str
    conversation_id: int
    citations: list[Citation]