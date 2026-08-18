from typing import Optional

from pydantic import BaseModel, Field

from ..config import settings
from ..models.schemas import RetrievedChunk

OUT_OF_SCOPE_MAX_SCORE = 0.3


class GuardrailResult(BaseModel):
    allowed: bool
    maxScore: float
    reason: Optional[str] = Field(default=None)


class GuardrailService:
    def checkConfidence(self, retrievedChunks: list[RetrievedChunk]) -> GuardrailResult:
        if not retrievedChunks:
            return GuardrailResult(allowed=False, maxScore=0.0, reason="no_context")

        maxScore = max(chunk.score for chunk in retrievedChunks)
        if maxScore < settings.confidenceThreshold:
            if maxScore < OUT_OF_SCOPE_MAX_SCORE:
                reason = "out_of_scope"
            else:
                reason = "low_confidence"
            return GuardrailResult(allowed=False, maxScore=maxScore, reason=reason)

        return GuardrailResult(allowed=True, maxScore=maxScore, reason=None)
