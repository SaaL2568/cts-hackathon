from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class IntentResult(BaseModel):
    intent: Literal["chitchat", "domain_query"]
    reason: Optional[str] = None


class SanitizationResult(BaseModel):
    cleaned: str
    flagged: bool
    flaggedPatterns: list[str] = Field(default_factory=list)



class Chunk(BaseModel):
    chunkId: str
    docName: str
    pageNum: int
    section: Optional[str] = None
    text: str
    embedding: Optional[list[float]] = None


class RetrievedChunk(BaseModel):
    chunkId: str
    docName: str
    pageNum: int
    section: Optional[str] = None
    text: str
    score: float


class Citation(BaseModel):
    docName: str
    pageNum: int
    snippet: str


class UploadDocumentResponse(BaseModel):
    docName: str
    chunksIndexed: int
    pagesProcessed: int


class ListDocumentsResponse(BaseModel):
    documents: list[str]


class LookupResult(BaseModel):
    docName: str
    chunksIndexed: int
    pagesProcessed: int
    alreadyIndexed: bool = False


class QueryRequest(BaseModel):
    sessionId: str
    question: str


class QueryResponse(BaseModel):
    sessionId: str
    answer: str
    citations: list[Citation]
    confidence: float
    refused: bool
    refusalReason: Optional[str] = None


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    citations: list[Citation] = Field(default_factory=list)
    refused: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CreateSessionResponse(BaseModel):
    sessionId: str


class SessionHistoryResponse(BaseModel):
    sessionId: str
    turns: list[ChatTurn]


class ListSessionsResponse(BaseModel):
    sessionIds: list[str]


class SummarizedSection(BaseModel):
    pageNum: int
    section: Optional[str] = None
    summaryText: str
    sourceCharCount: int
