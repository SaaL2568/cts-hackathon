import re

from ..models.schemas import SanitizationResult

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous\s+)?instructions",
    r"ignore\s+the\s+system\s+prompt",
    r"disregard\s+the\s+above",
    r"you\s+are\s+now\b",
    r"print\s+your\s+instructions",
    r"reveal\s+your\s+prompt",
    r"system\s*:",
    r"override\s+(system\s+)?prompt",
    r"forget\s+(all\s+)?prior\s+instructions",
]

INJECTION_REGEXES = [
    (pattern, re.compile(pattern, re.IGNORECASE))
    for pattern in INJECTION_PATTERNS
]


class PromptSanitizerService:
    def sanitize(self, text: str) -> SanitizationResult:
        if not text:
            return SanitizationResult(cleaned="", flagged=False, flaggedPatterns=[])

        cleanedText = text
        flagged = False
        flaggedPatterns: list[str] = []

        for rawPattern, regex in INJECTION_REGEXES:
            if regex.search(cleanedText):
                flagged = True
                flaggedPatterns.append(rawPattern)
                cleanedText = regex.sub("[removed prompt instruction]", cleanedText)

        return SanitizationResult(
            cleaned=cleanedText.strip(),
            flagged=flagged,
            flaggedPatterns=flaggedPatterns,
        )
