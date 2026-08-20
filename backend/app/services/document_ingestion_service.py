import re
import uuid
from pathlib import Path
from typing import Optional

from pdfplumber import open as open_pdf

from ..config import settings
from ..errors import IngestionError
from ..models.schemas import Chunk, SummarizedSection
from .embedding_service import EmbeddingService
from .pdf_parsing_utils import isSectionHeader, segmentBySections
from .vector_store_client import getCollection

_WHITESPACE_PATTERN = re.compile(r"\s+")
_WORD_PATTERN = re.compile(r"\S+")


class DocumentIngestionService:
    def __init__(self, embeddingService: EmbeddingService):
        self.embeddingService = embeddingService

    def ingestDocument(self, pdfPath: str, docName: str) -> tuple[int, int]:
        chunks = self.parsePdfToChunks(pdfPath, docName)
        embeddedChunks = self.embedChunks(chunks)
        self.storeChunks(embeddedChunks)
        pagesProcessed = len({chunk.pageNum for chunk in chunks})
        return len(chunks), pagesProcessed

    def ingestSummarizedSections(
        self, sections: list[SummarizedSection], docName: str
    ) -> tuple[int, int]:
        chunks: list[Chunk] = []
        for section in sections:
            normalizedText = _WHITESPACE_PATTERN.sub(" ", section.summaryText).strip()
            if not normalizedText:
                continue
            sectionChunks = self._chunkSegment(
                section=section.section,
                text=normalizedText,
                docName=docName,
                pageNum=section.pageNum,
            )
            chunks.extend(sectionChunks)
        embeddedChunks = self.embedChunks(chunks)
        self.storeChunks(embeddedChunks)
        pagesProcessed = len({s.pageNum for s in sections})
        return len(chunks), pagesProcessed

    def parsePdfToChunks(self, pdfPath: str, docName: str) -> list[Chunk]:
        path = Path(pdfPath)
        if not path.exists():
            raise IngestionError(f"PDF file not found: {pdfPath}")
        if not path.suffix.lower() == ".pdf":
            raise IngestionError(f"Not a PDF file: {pdfPath}")

        chunks: list[Chunk] = []
        try:
            with open_pdf(str(path)) as pdf:
                for pageIndex, page in enumerate(pdf.pages, start=1):
                    rawText = page.extract_text()
                    if not rawText or not rawText.strip():
                        continue
                    pageChunks = self._chunkPageText(
                        rawText, docName=docName, pageNum=pageIndex
                    )
                    chunks.extend(pageChunks)
        except IngestionError:
            raise
        except Exception as exc:
            raise IngestionError(f"Failed to parse PDF {pdfPath}: {exc}") from exc

        if not chunks:
            raise IngestionError(
                f"No extractable text found in {pdfPath}. "
                "Scanned/image-only PDFs are not supported."
            )
        return chunks

    def _chunkPageText(self, text: str, docName: str, pageNum: int) -> list[Chunk]:
        segments = self._segmentBySections(text)
        chunks: list[Chunk] = []
        for section, segmentText in segments:
            normalizedSegment = _WHITESPACE_PATTERN.sub(" ", segmentText).strip()
            if not normalizedSegment:
                continue
            chunks.extend(
                self._chunkSegment(
                    section=section,
                    text=normalizedSegment,
                    docName=docName,
                    pageNum=pageNum,
                )
            )
        return chunks

    def _segmentBySections(self, text: str) -> list[tuple[Optional[str], str]]:
        return segmentBySections(text)

    def _chunkSegment(
        self,
        section: Optional[str],
        text: str,
        docName: str,
        pageNum: int,
    ) -> list[Chunk]:
        words = _WORD_PATTERN.findall(text)
        if not words:
            return []
        chunkSize = settings.maxChunkTokens
        overlap = settings.chunkOverlap
        step = max(1, chunkSize - overlap)
        chunks: list[Chunk] = []
        index = 0
        while index < len(words):
            window = words[index : index + chunkSize]
            chunks.append(
                Chunk(
                    chunkId=str(uuid.uuid4()),
                    docName=docName,
                    pageNum=pageNum,
                    section=section,
                    text=" ".join(window),
                )
            )
            index += step
            if index >= len(words):
                break
        return chunks

    def embedChunks(self, chunks: list[Chunk]) -> list[Chunk]:
        if not chunks:
            return chunks
        texts = [chunk.text for chunk in chunks]
        embeddings = self.embeddingService.embedTexts(texts)
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
        return chunks

    def storeChunks(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        collection = getCollection()
        docName = chunks[0].docName
        collection.delete(where={"docName": docName})
        collection.add(
            ids=[chunk.chunkId for chunk in chunks],
            embeddings=[chunk.embedding for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            metadatas=[
                {
                    "docName": chunk.docName,
                    "pageNum": chunk.pageNum,
                    "section": chunk.section or "",
                }
                for chunk in chunks
            ],
        )
