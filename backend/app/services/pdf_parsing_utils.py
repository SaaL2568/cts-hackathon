import re
from typing import Optional

_SECTION_HEADER_PATTERN = re.compile(r"^[A-Z][A-Z0-9 ,.'()\/&\-]{4,}$")


def isSectionHeader(line: str) -> bool:
    stripped = line.strip()
    if len(stripped) < 5:
        return False
    if not _SECTION_HEADER_PATTERN.match(stripped):
        return False
    upperCount = sum(1 for char in stripped if char.isalpha())
    return (
        upperCount > 0
        and upperCount / max(1, sum(1 for char in stripped if char.isalnum())) >= 0.85
    )


def segmentBySections(text: str) -> list[tuple[Optional[str], str]]:
    rawLines = text.split("\n")
    segments: list[tuple[Optional[str], list[str]]] = []
    currentSection: Optional[str] = None
    currentLines: list[str] = []

    def flush():
        if currentLines:
            segments.append((currentSection, currentLines))

    for line in rawLines:
        trimmed = line.strip()
        if not trimmed:
            continue
        if isSectionHeader(trimmed):
            flush()
            currentSection = trimmed
            currentLines = [trimmed]
        else:
            currentLines.append(trimmed)
    flush()

    return [(section, " ".join(words)) for section, words in segments]
