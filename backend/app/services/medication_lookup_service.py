import logging
import re
from pathlib import Path
from typing import Optional

import httpx

from ..config import settings
from ..models.schemas import LookupResult
from .document_ingestion_service import DocumentIngestionService
from .vector_store_client import docExists

_CAPITALIZED_RUN_PATTERN = re.compile(
    r"\b[A-Z][a-z0-9-]+(?:[ -][A-Z][a-z0-9-]+){0,2}\b"
)
_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9-]*")

_STOPWORDS = {
    # Question words
    "about", "all", "also", "an", "and", "any", "are", "ask", "been", "being",
    "between", "but", "by", "can", "cause", "causes", "caused", "could", "did",
    "do", "does", "dose", "dosage", "drug", "drugs",
    # Common verbs / auxiliary
    "effects", "for", "from", "get", "gets", "give", "given", "good", "has",
    "have", "help", "her", "him", "his", "how", "if", "in", "information",
    "interactions", "into", "is", "it", "its",
    # Medical-context generics
    "label", "labels", "list", "listed", "many", "me", "medicine", "medication",
    "medications", "milligrams", "mg", "much", "my",
    # Prepositions / articles
    "of", "on", "one", "or", "other", "our",
    # P-Z
    "prescribing", "please", "question", "recommended", "recommend", "safe",
    "safety", "should", "side", "some", "tablet", "tablets", "take", "taken",
    "tell", "that", "the", "them", "there", "these", "they", "this", "those",
    "to", "treatment", "treatments", "use", "used", "using",
    "want", "was", "we", "what", "when", "where", "which", "while",
    "who", "why", "will", "with", "warnings", "whats", "you", "your",
}


logger = logging.getLogger(__name__)


class MedicationLookupService:
    def __init__(self, documentIngestionService: DocumentIngestionService):
        self.documentIngestionService = documentIngestionService

    def findAndIngest(self, query: str) -> Optional[LookupResult]:
        if not settings.publicLookupEnabled:
            return None

        keywords = self._extractDrugKeywords(query)
        logger.info("Extracted drug keywords from query %r: %s", query, keywords)
        for term in keywords:
            logger.info("Searching OpenFDA for term: %r", term)
            info = self._safeSearch(term)
            if not info:
                logger.info("OpenFDA: no result for %r", term)
                continue
            logger.info("OpenFDA found: docName=%r setId=%r", info.get('docName'), info.get('setId'))
            pdfPath = self._safeDownload(info)
            if not pdfPath:
                logger.warning("PDF download failed for %r", info.get('docName'))
                continue
            logger.info("PDF ready at: %s", pdfPath)
            alreadyIndexed = docExists(info["docName"])
            if alreadyIndexed:
                logger.info("Document already indexed: %r", info['docName'])
                return LookupResult(
                    docName=info["docName"],
                    chunksIndexed=0,
                    pagesProcessed=0,
                    alreadyIndexed=True,
                )
            try:
                chunkCount, pagesProcessed = self.documentIngestionService.ingestDocument(
                    str(pdfPath), info["docName"]
                )
                logger.info("Ingested %r: %d chunks, %d pages", info['docName'], chunkCount, pagesProcessed)
            except Exception as exc:
                logger.error("Ingestion failed for %r: %s", info.get('docName'), exc)
                continue
            return LookupResult(
                docName=info["docName"],
                chunksIndexed=chunkCount,
                pagesProcessed=pagesProcessed,
            )
        logger.info("Auto-lookup exhausted all keywords with no result")
        return None

    def _extractDrugKeywords(self, query: str) -> list[str]:
        candidates: list[str] = []
        seen: set[str] = set()

        for token in _TOKEN_PATTERN.findall(query):
            if len(token) < 3:
                continue
            key = token.lower()
            if key in _STOPWORDS or key in seen:
                continue
            candidates.append(token)
            seen.add(key)

        for match in _CAPITALIZED_RUN_PATTERN.finditer(query):
            phrase = match.group(0)
            key = phrase.lower()
            if key in _STOPWORDS or key in seen:
                continue
            candidates.append(phrase)
            seen.add(key)

        return candidates

    def _safeSearch(self, term: str) -> Optional[dict]:
        try:
            return self._searchOpenFda(term)
        except Exception:
            return None

    def _searchOpenFda(self, term: str) -> Optional[dict]:
        quoted = term.replace('"', '')
        searches = [f'openfda.brand_name:"{quoted}"', f'openfda.generic_name:"{quoted}"']
        with httpx.Client(timeout=settings.publicLookupTimeoutSeconds) as client:
            for search in searches:
                try:
                    response = client.get(
                        settings.openfdaLabelUrl,
                        params={"search": search, "limit": 1},
                    )
                    if response.status_code == 404:
                        continue
                    response.raise_for_status()
                except httpx.HTTPError:
                    continue
                label = (response.json().get("results") or [None])[0]
                if not label:
                    continue
                openfda = label.get("openfda") or {}
                setIds = openfda.get("spl_set_id") or openfda.get("set_id") or []
                if not setIds:
                    continue
                brand = (openfda.get("brand_name") or [quoted])[0]
                generic = (openfda.get("generic_name") or [None])[0]
                if generic and generic.lower() != brand.lower():
                    docName = f"{brand} ({generic})"
                else:
                    docName = brand
                return {"setId": setIds[0], "docName": docName, "brand": brand, "generic": generic}
        return None

    def _safeDownload(self, info: dict) -> Optional[Path]:
        try:
            return self._downloadLabelPdf(info)
        except Exception:
            return None

    def _downloadLabelPdf(self, info: dict) -> Path:
        safeName = re.sub(r"[^A-Za-z0-9_-]+", "-", info["docName"]).strip("-").lower()
        settings.pdfUploadDir.mkdir(parents=True, exist_ok=True)
        path = settings.pdfUploadDir / f"{safeName}.pdf"
        if path.exists() and path.stat().st_size > 0:
            return path

        url = f"{settings.dailymedPdfUrl}?setid={info['setId']}&type=pdf"
        with httpx.Client(timeout=settings.publicLookupTimeoutSeconds) as client:
            response = client.get(url, follow_redirects=True)
            response.raise_for_status()
            path.write_bytes(response.content)
        return path
