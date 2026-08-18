from typing import Optional

import httpx

from ..config import settings
from ..errors import AnswerGenerationError
from ..models.schemas import ChatTurn, RetrievedChunk

SYSTEM_PROMPT = (
    "You are a medical information assistant that answers questions about drug "
    "prescribing information. Your answers must be grounded exclusively in the "
    "provided context blocks below.\n"
    "Rules:\n"
    "1. Answer only using the context blocks. Do not use outside knowledge.\n"
    "2. Cite every factual claim inline in the format [doc name, page number] "
    "using a context block you actually used.\n"
    "3. If the context does not contain enough information to answer the "
    "question confidently, reply with exactly the prefix 'REFUSED: ' followed "
    "by a short explanation.\n"
    "4. Never invent dosages, indications, warnings, or any medical claim.\n"
    "5. Keep the answer concise and directly on topic.\n\n"
    "Context blocks:\n{context}"
)


class AnswerGenerator:
    def generateAnswerWithCitations(
        self,
        query: str,
        retrievedChunks: list[RetrievedChunk],
        history: list[ChatTurn],
    ) -> tuple[str, bool, Optional[str]]:
        context = self._buildContext(retrievedChunks)
        systemPrompt = SYSTEM_PROMPT.format(context=context)

        messages: list[dict] = []
        for turn in history[-settings.maxHistoryTurns :]:
            messages.append({"role": turn.role, "content": turn.content})
        messages.append({"role": "user", "content": query})

        answer = self._callOllama(systemPrompt, messages)
        stripped = answer.strip()
        refused = False
        refusalReason: Optional[str] = None
        if stripped.upper().startswith("REFUSED"):
            refused = True
            refusalReason = stripped[len("REFUSED") :].strip(" :")
            answer = f"I cannot answer this from the available information.{(' ' + refusalReason) if refusalReason else ''}"
        return answer, refused, refusalReason

    def _buildContext(self, retrievedChunks: list[RetrievedChunk]) -> str:
        if not retrievedChunks:
            return "(no context available)"
        blocks = []
        for index, chunk in enumerate(retrievedChunks, start=1):
            citation = f"[{chunk.docName}, page {chunk.pageNum}]"
            sectionLabel = f" (section: {chunk.section})" if chunk.section else ""
            blocks.append(f"Context {index} {citation}{sectionLabel}:\n{chunk.text}")
        return "\n\n".join(blocks)

    def _callOllama(self, systemPrompt: str, messages: list[dict]) -> str:
        url = f"{settings.ollamaBaseUrl.rstrip('/')}/api/chat"
        payload = {
            "model": settings.ollamaModel,
            "messages": [{"role": "system", "content": systemPrompt}, *messages],
            "stream": False,
            "options": {"temperature": 0.1},
        }
        try:
            response = httpx.post(
                url,
                json=payload,
                timeout=settings.ollamaTimeoutSeconds,
            )
            response.raise_for_status()
        except Exception as exc:
            raise AnswerGenerationError(
                f"Ollama request failed. Is Ollama running and the model "
                f"'{settings.ollamaModel}' pulled? Details: {exc}"
            ) from exc

        data = response.json()
        message = data.get("message") or {}
        content = message.get("content") or ""
        if not content.strip():
            raise AnswerGenerationError("Ollama returned an empty response.")
        return content
