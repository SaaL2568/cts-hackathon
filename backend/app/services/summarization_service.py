import base64
import io
import logging
from pathlib import Path
from typing import Optional

httpx = None
try:
    import httpx
except ImportError:
    pass

from pdfplumber import open as open_pdf

from ..config import settings
from ..errors import SummarizationError
from ..models.schemas import SummarizedSection
from .pdf_parsing_utils import segmentBySections

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Summarize the following FDA drug label section concisely. "
    "Preserve exact numeric dosages, warnings, and contraindications verbatim — "
    "do not round or paraphrase numbers."
)


class SummarizationService:
    def summarizeDocument(
        self, pdfPath: str, docName: str
    ) -> list[SummarizedSection]:
        path = Path(pdfPath)
        if not path.exists():
            raise SummarizationError(f"PDF file not found: {pdfPath}")

        if settings.summarizerProvider == "off" or not settings.openrouterApiKey:
            logger.info("Summarization provider is off or API key missing; returning raw sections.")
            return self._extractRawSections(path)

        summarizedSections: list[SummarizedSection] = []
        try:
            with open_pdf(str(path)) as pdf:
                for pageIndex, page in enumerate(pdf.pages, start=1):
                    rawText = page.extract_text() or ""
                    hasImages = bool(page.images and len(page.images) > 0)
                    base64Image: Optional[str] = None
                    if hasImages:
                        try:
                            imageBytes = self._extractPageImage(page)
                            base64Image = base64.b64encode(imageBytes).decode("utf-8")
                        except Exception as imgExc:
                            logger.warning("Failed to render page %d image: %s", pageIndex, imgExc)

                    segments = segmentBySections(rawText) if rawText.strip() else []
                    if not segments and rawText.strip():
                        segments = [(None, rawText)]

                    if not segments and hasImages:
                        segments = [(None, "")]

                    for section, segmentText in segments:
                        sourceLen = len(segmentText)
                        try:
                            if hasImages and base64Image:
                                userContent = [
                                    {
                                        "type": "text",
                                        "text": (
                                            "Describe any tables, charts, or warnings shown in this drug label page image.\n"
                                            f"Section: {section or 'General'}\nText: {segmentText}"
                                        ),
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/png;base64,{base64Image}"
                                        },
                                    },
                                ]
                            else:
                                userContent = f"Section: {section or 'General'}\nText: {segmentText}"

                            summaryText = self._callOpenRouter(SYSTEM_PROMPT, userContent)
                            summaryLen = len(summaryText)
                            reduction = (1.0 - (summaryLen / max(1, sourceLen))) * 100.0
                            logger.info(
                                "Summarized %s p.%d section %r: %d -> %d chars (%.1f%% reduction)",
                                docName, pageIndex, section, sourceLen, summaryLen, reduction
                            )
                            summarizedSections.append(
                                SummarizedSection(
                                    pageNum=pageIndex,
                                    section=section,
                                    summaryText=summaryText,
                                    sourceCharCount=sourceLen,
                                )
                            )
                        except Exception as secExc:
                            logger.warning(
                                "Summarization call failed for %s p.%d section %r (%s). Falling back to raw text.",
                                docName, pageIndex, section, secExc
                            )
                            summarizedSections.append(
                                SummarizedSection(
                                    pageNum=pageIndex,
                                    section=section,
                                    summaryText=segmentText,
                                    sourceCharCount=sourceLen,
                                )
                            )
        except Exception as exc:
            logger.warning("Document summarization failed for %s: %s. Falling back to raw sections.", docName, exc)
            return self._extractRawSections(path)

        if not summarizedSections:
            return self._extractRawSections(path)

        return summarizedSections

    def _extractRawSections(self, path: Path) -> list[SummarizedSection]:
        sections: list[SummarizedSection] = []
        try:
            with open_pdf(str(path)) as pdf:
                for pageIndex, page in enumerate(pdf.pages, start=1):
                    rawText = page.extract_text() or ""
                    if not rawText.strip():
                        continue
                    segments = segmentBySections(rawText)
                    for section, segmentText in segments:
                        sections.append(
                            SummarizedSection(
                                pageNum=pageIndex,
                                section=section,
                                summaryText=segmentText,
                                sourceCharCount=len(segmentText),
                            )
                        )
        except Exception as exc:
            logger.error("Failed to extract raw sections from %s: %s", path, exc)
        return sections

    def _extractPageImage(self, page) -> bytes:
        pageImage = page.to_image(resolution=150)
        buffer = io.BytesIO()
        pageImage.original.save(buffer, format="PNG")
        return buffer.getvalue()

    def _callOpenRouter(self, systemPrompt: str, userContent) -> str:
        if not settings.openrouterApiKey:
            raise SummarizationError("OPENROUTER_API_KEY is not set.")

        import httpx

        url = f"{settings.openrouterBaseUrl.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.openrouterApiKey}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.openrouterModel,
            "messages": [
                {"role": "system", "content": systemPrompt},
                {"role": "user", "content": userContent},
            ],
            "temperature": 0.1,
        }
        response = httpx.post(
            url,
            json=payload,
            headers=headers,
            timeout=settings.publicLookupTimeoutSeconds,
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise SummarizationError("OpenRouter response contained no choices.")
        content = (choices[0].get("message") or {}).get("content") or ""
        if not content.strip():
            raise SummarizationError("OpenRouter response contained empty content.")
        return content.strip()
