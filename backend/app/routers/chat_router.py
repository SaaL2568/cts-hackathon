import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from ..config import settings
from ..dependencies import (
    answerGenerator,
    chatSessionManager,
    guardrailService,
    intentClassifierService,
    medicationLookupService,
    promptSanitizerService,
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
logger = logging.getLogger(__name__)

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

    history = chatSessionManager.getSessionHistory(sessionId)

    intentResult = intentClassifierService.classify(question)
    if intentResult.intent == "chitchat":
        logger.info("Chit-chat intent detected for question: %r", question)
        userTurn = ChatTurn(role="user", content=question)
        chatSessionManager.appendTurn(sessionId, userTurn)

        loop = asyncio.get_running_loop()
        chitchatAnswer = await loop.run_in_executor(
            None,
            answerGenerator.generateChitchatAnswer,
            question,
            history,
        )

        assistantTurn = ChatTurn(role="assistant", content=chitchatAnswer, citations=[], refused=False)
        chatSessionManager.appendTurn(sessionId, assistantTurn)

        return QueryResponse(
            sessionId=sessionId,
            answer=chitchatAnswer,
            citations=[],
            confidence=1.0,
            refused=False,
            refusalReason=None,
        )

    sanitized = promptSanitizerService.sanitize(question)
    queryText = sanitized.cleaned if sanitized.cleaned else question

    userTurn = ChatTurn(role="user", content=question)
    chatSessionManager.appendTurn(sessionId, userTurn)

    result = await _generateAnswer(queryText, history)
    logger.info(
        "Initial answer: allowed=%s refused=%s confidence=%.3f",
        result["allowed"],
        result["refused"],
        result["guardResult"].maxScore,
    )

    needsPublicLookup = settings.publicLookupEnabled and (
        not result["allowed"] or result["refused"]
    )
    if needsPublicLookup:
        logger.info("Auto-lookup triggered for query: %r", queryText)
        lookupResult = await asyncio.get_running_loop().run_in_executor(
            None, medicationLookupService.findAndIngest, queryText
        )
        if lookupResult:
            logger.info(
                "Lookup succeeded: docName=%r chunks=%d alreadyIndexed=%s",
                lookupResult.docName,
                lookupResult.chunksIndexed,
                lookupResult.alreadyIndexed,
            )
            result = await _generateAnswer(queryText, history)
            logger.info(
                "Post-lookup answer: allowed=%s refused=%s confidence=%.3f",
                result["allowed"],
                result["refused"],
                result["guardResult"].maxScore,
            )
        else:
            logger.info("Auto-lookup returned no result for query: %r", queryText)

    if not result["allowed"]:
        guardResult = result["guardResult"]
        refusalReason = guardResult.reason or "low_confidence"
        answer = _REFUSAL_MESSAGES.get(refusalReason, _REFUSAL_MESSAGES["low_confidence"])
        assistantTurn = ChatTurn(role="assistant", content=answer, refused=True)
        chatSessionManager.appendTurn(sessionId, assistantTurn)
        return QueryResponse(
            sessionId=sessionId,
            answer=answer,
            citations=[],
            confidence=guardResult.maxScore,
            refused=True,
            refusalReason=refusalReason,
        )

    retrievedChunks = result["retrievedChunks"]

    # If the LLM itself refused, don't show citations from unrelated documents.
    if result["refused"]:
        refusalReason = result["refusalReason"] or "low_confidence"
        assistantTurn = ChatTurn(
            role="assistant",
            content=result["answer"],
            citations=[],
            refused=True,
        )
        chatSessionManager.appendTurn(sessionId, assistantTurn)
        return QueryResponse(
            sessionId=sessionId,
            answer=result["answer"],
            citations=[],
            confidence=result["guardResult"].maxScore,
            refused=True,
            refusalReason=refusalReason,
        )

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
        content=result["answer"],
        citations=citations,
        refused=False,
    )
    chatSessionManager.appendTurn(sessionId, assistantTurn)

    return QueryResponse(
        sessionId=sessionId,
        answer=result["answer"],
        citations=citations,
        confidence=result["guardResult"].maxScore,
        refused=False,
        refusalReason=None,
    )


@router.get("/sessionHistory/{sessionId}", response_model=SessionHistoryResponse)
def sessionHistory(sessionId: str) -> SessionHistoryResponse:
    turns = chatSessionManager.getSessionHistory(sessionId)
    return SessionHistoryResponse(sessionId=sessionId, turns=turns)


async def _generateAnswer(question: str, history: list[ChatTurn]) -> dict:
    loop = asyncio.get_running_loop()

    try:
        retrievedChunks = await loop.run_in_executor(
            None, retrievalService.retrieveRelevantChunks, question
        )
    except RetrievalError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    guardResult = guardrailService.checkConfidence(retrievedChunks)
    if not guardResult.allowed:
        return {
            "allowed": False,
            "guardResult": guardResult,
            "retrievedChunks": retrievedChunks,
            "answer": None,
            "refused": True,
            "refusalReason": guardResult.reason,
        }

    try:
        answer, refused, refusalReason = await loop.run_in_executor(
            None,
            answerGenerator.generateAnswerWithCitations,
            question,
            retrievedChunks,
            history,
        )
    except AnswerGenerationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {
        "allowed": True,
        "guardResult": guardResult,
        "retrievedChunks": retrievedChunks,
        "answer": answer,
        "refused": refused,
        "refusalReason": refusalReason,
    }


def _trimSnippet(text: str) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= _SNIPPET_MAX_CHARS:
        return normalized
    return normalized[:_SNIPPET_MAX_CHARS].rstrip() + "..."
