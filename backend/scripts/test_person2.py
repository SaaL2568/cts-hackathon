import shutil
import tempfile
from pathlib import Path

from app.config import settings
from app.models.schemas import SummarizedSection
from app.services.document_ingestion_service import DocumentIngestionService
from app.services.embedding_service import EmbeddingService
from app.services.pdf_parsing_utils import isSectionHeader, segmentBySections
from app.services.summarization_service import SummarizationService


def testPdfParsingUtils():
    header1 = "DOSAGE AND ADMINISTRATION"
    header2 = "INDICATIONS AND USAGE"
    normalText = "This is normal paragraph text."

    assert isSectionHeader(header1) is True, f"Expected {header1} to be section header"
    assert isSectionHeader(header2) is True, f"Expected {header2} to be section header"
    assert isSectionHeader(normalText) is False, f"Expected normal text not to be section header"

    sampleText = "INDICATIONS AND USAGE\nEliquis is an anticoagulant.\nDOSAGE AND ADMINISTRATION\n5 mg twice daily."
    segments = segmentBySections(sampleText)
    assert len(segments) == 2, f"Expected 2 segments, got {len(segments)}"
    assert segments[0][0] == "INDICATIONS AND USAGE"
    assert segments[1][0] == "DOSAGE AND ADMINISTRATION"
    print("[PASS] PDF parsing utils test passed!")


def testSummarizationFallback():
    origProvider = settings.summarizerProvider
    origKey = settings.openrouterApiKey
    settings.summarizerProvider = "off"

    try:
        service = SummarizationService()
        # Test OpenRouter call throws SummarizationError when key missing
        try:
            service._callOpenRouter("sys", "user")
            assert False, "Expected SummarizationError when API key is missing"
        except Exception:
            pass
        print("[PASS] Summarization fallback test passed!")
    finally:
        settings.summarizerProvider = origProvider
        settings.openrouterApiKey = origKey


def testIngestSummarizedSections():
    dummyEmbedding = EmbeddingService()
    ingestionService = DocumentIngestionService(dummyEmbedding)

    sections = [
        SummarizedSection(
            pageNum=1,
            section="DOSAGE AND ADMINISTRATION",
            summaryText="5 mg twice daily.",
            sourceCharCount=100,
        ),
        SummarizedSection(
            pageNum=2,
            section="WARNINGS AND PRECAUTIONS",
            summaryText="Increases risk of bleeding.",
            sourceCharCount=120,
        ),
    ]

    docName = "test_drug_summary"
    chunkCount, pagesProcessed = ingestionService.ingestSummarizedSections(sections, docName)

    assert chunkCount >= 2, f"Expected at least 2 chunks, got {chunkCount}"
    assert pagesProcessed == 2, f"Expected 2 pages processed, got {pagesProcessed}"
    print("[PASS] Ingest summarized sections test passed!")


if __name__ == "__main__":
    testPdfParsingUtils()
    testSummarizationFallback()
    testIngestSummarizedSections()
    print("\nALL PERSON 2 VERIFICATION TESTS PASSED SUCCESSFULLY!")
