import asyncio

from fastapi import APIRouter, HTTPException

from ..dependencies import (
    answerGenerator,
    chatSessionManager,
    guardrailService,
    retrievalService,
)
from ..errors import AnswerGenerationError, RetrievalError
from ..models.schemas import (
    ChatTurn,
    Citation,
    CreateSessionResponse,
    QueryRequest,
    QueryResponse,
    SessionHistoryResponse,
)

router = APIRouter(tags=["chat"])

_SNIPPET_MAX_CHARS = 200

_REFUSAL_MESSAGES = {
    "no_context": "I could not find any relevant information in the ingested documents.",
    "out_of_scope": "This question appears to be out of scope for the ingested documents.",
    "low_confidence": "I could not answer this question confidently based on the available information.",
}


@router.post("/createSession", response_model=CreateSessionResponse)
def createSession() -> CreateSessionResponse:
    sessionId = chatSessionManager.createSession()
    return CreateSessionResponse(sessionId=sessionId)


@router.post("/queryChat", response_model=QueryResponse)
async def queryChat(request: QueryRequest) -> QueryResponse:
    sessionId = request.sessionId.strip()
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    try:
        retrievedChunks = await asyncio.get_running_loop().run_in_executor(
            None, retrievalService.retrieveRelevantChunks, question
        )
    except RetrievalError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    guardResult = guardrailService.checkConfidence(retrievedChunks)
    history = chatSessionManager.getSessionHistory(sessionId)

    userTurn = ChatTurn(role="user", content=question)
    chatSessionManager.appendTurn(sessionId, userTurn)

    if not guardResult.allowed:
        refusalReason = guardResult.reason or "low_confidence"
        answer = _REFUSAL_MESSAGES.get(refusalReason, _REFUSAL_MESSAGES["low_confidence"])
        assistantTurn = ChatTurn(
            role="assistant",
            content=answer,
            refused=True,
        )
        chatSessionManager.appendTurn(sessionId, assistantTurn)
        return QueryResponse(
            sessionId=sessionId,
            answer=answer,
            citations=[],
            confidence=guardResult.maxScore,
            refused=True,
            refusalReason=refusalReason,
        )

    try:
        answer, refused, refusalReason = await asyncio.get_running_loop().run_in_executor(
            None,
            answerGenerator.generateAnswerWithCitations,
            question,
            retrievedChunks,
            history,
        )
    except AnswerGenerationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    citations = [
        Citation(
            docName=chunk.docName,
            pageNum=chunk.pageNum,
            snippet=_trimSnippet(chunk.text),
        )
        for chunk in retrievedChunks
    ]

    assistantTurn = ChatTurn(
        role="assistant",
        content=answer,
        citations=citations,
        refused=refused,
    )
    chatSessionManager.appendTurn(sessionId, assistantTurn)

    return QueryResponse(
        sessionId=sessionId,
        answer=answer,
        citations=citations,
        confidence=guardResult.maxScore,
        refused=refused,
        refusalReason=refusalReason,
    )


@router.get("/sessionHistory/{sessionId}", response_model=SessionHistoryResponse)
def sessionHistory(sessionId: str) -> SessionHistoryResponse:
    turns = chatSessionManager.getSessionHistory(sessionId)
    return SessionHistoryResponse(sessionId=sessionId, turns=turns)


def _trimSnippet(text: str) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= _SNIPPET_MAX_CHARS:
        return normalized
    return normalized[:_SNIPPET_MAX_CHARS].rstrip() + "..."
