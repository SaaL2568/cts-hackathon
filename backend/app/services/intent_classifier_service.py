import re
from typing import Optional

from ..models.schemas import IntentResult

CHITCHAT_PATTERNS = [
    r"^(hi|hello|hey|yo|greetings|good\s+(morning|afternoon|evening))\b",
    r"^(thanks|thank\s+you|thx|thank\s+you\s+so\s+much)\b",
    r"^(bye|goodbye|see\s+ya|farewell)\b",
    r"^(who\s+are\s+you|what\s+can\s+you\s+do|help|what\s+are\s+your\s+capabilities)\b",
    r"^(how\s+are\s+you|what's\s+up|whats\s+up)\b",
]

CHITCHAT_COMPILED = [re.compile(pattern, re.IGNORECASE) for pattern in CHITCHAT_PATTERNS]

MEDICAL_KEYWORDS = {
    "dose", "dosage", "indication", "indications", "side", "effect", "effects",
    "adverse", "reaction", "reactions", "warning", "warnings", "boxed",
    "contraindication", "contraindications", "precautions", "interaction",
    "interactions", "pharmacokinetics", "storage", "store", "administration",
    "administer", "overdose", "use", "uses", "drug", "medicine", "medication",
    "pill", "tablet", "capsule", "injection", "patient", "treatment", "treat",
    "prescribe", "prescribing", "label", "fda",
}

_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9-]*")
_CAPITALIZED_TERM_PATTERN = re.compile(r"\b[A-Z][a-z0-9-]{2,}\b")


class IntentClassifierService:
    def classify(self, question: str) -> IntentResult:
        cleaned = question.strip()
        if not cleaned:
            return IntentResult(intent="chitchat", reason="empty input")

        # Check explicit regex patterns
        for pattern in CHITCHAT_COMPILED:
            if pattern.search(cleaned):
                tokens = set(t.lower() for t in _TOKEN_PATTERN.findall(cleaned))
                if not (tokens & MEDICAL_KEYWORDS):
                    return IntentResult(intent="chitchat", reason="matched chitchat pattern")

        tokens = _TOKEN_PATTERN.findall(cleaned)
        tokenCount = len(tokens)

        # Short input check (< 4 tokens) with no capitalized drug-like term and no medical keyword
        if tokenCount < 4:
            hasMedicalKeyword = any(t.lower() in MEDICAL_KEYWORDS for t in tokens)
            hasCapitalizedTerm = bool(_CAPITALIZED_TERM_PATTERN.search(cleaned))
            if not hasMedicalKeyword and not hasCapitalizedTerm:
                return IntentResult(intent="chitchat", reason="short non-medical input")

        return IntentResult(intent="domain_query", reason="domain query")
