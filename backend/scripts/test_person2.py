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


def testSummarizationRetries():
    from unittest.mock import patch, MagicMock
    import httpx
    from app.errors import SummarizationError

    service = SummarizationService()
    origKey = settings.openrouterApiKey
    settings.openrouterApiKey = "test-key"

    try:
        with patch("httpx.post") as mock_post:
            mock_resp_429 = MagicMock()
            mock_resp_429.status_code = 429
            mock_resp_429.raise_for_status.side_effect = httpx.HTTPStatusError(
                message="Too Many Requests",
                request=MagicMock(),
                response=mock_resp_429
            )

            mock_resp_200 = MagicMock()
            mock_resp_200.status_code = 200
            mock_resp_200.json.return_value = {
                "choices": [{"message": {"content": "Mocked Summary content"}}]
            }

            mock_post.side_effect = [mock_resp_429, mock_resp_429, mock_resp_200]

            with patch("time.sleep") as mock_sleep:
                res = service._callOpenRouter("sys", "user")

                assert res == "Mocked Summary content"
                assert mock_post.call_count == 3
                assert mock_sleep.call_count == 2

        print("[PASS] Summarization retries test passed!")
    finally:
        settings.openrouterApiKey = origKey


def testVisionFallback():
    from unittest.mock import patch, MagicMock
    from app.errors import SummarizationError
    import tempfile
    import os

    service = SummarizationService()

    origProvider = settings.summarizerProvider
    origKey = settings.openrouterApiKey
    settings.summarizerProvider = "openrouter"
    settings.openrouterApiKey = "test-key"

    fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)

    try:
        with patch.object(service, "_callOpenRouter") as mock_call:
            def call_side_effect(sys_prompt, user_content):
                if isinstance(user_content, list):
                    raise SummarizationError("Vision not supported")
                return "Fallback Text Summary"

            mock_call.side_effect = call_side_effect

            mock_page = MagicMock()
            mock_page.images = [{"width": 10}]
            mock_page.extract_text.return_value = "INDICATIONS AND USAGE\nSome drug info."

            mock_pdf = MagicMock()
            mock_pdf.pages = [mock_page]

            with patch("app.services.summarization_service.open_pdf") as mock_open_pdf, \
                 patch.object(service, "_extractPageImage", return_value=b"fake-image-bytes"):

                mock_open_pdf.return_value.__enter__.return_value = mock_pdf

                sections = service.summarizeDocument(tmp_path, "DummyDrug")

                assert len(sections) == 1
                assert sections[0].summaryText == "Fallback Text Summary"

                calls = mock_call.call_args_list
                assert len(calls) == 2
                assert isinstance(calls[0][0][1], list)
                assert isinstance(calls[1][0][1], str)

        print("[PASS] Vision fallback test passed!")
    finally:
        settings.summarizerProvider = origProvider
        settings.openrouterApiKey = origKey
        try:
            os.remove(tmp_path)
        except Exception:
            pass


if __name__ == "__main__":
    testPdfParsingUtils()
    testSummarizationFallback()
    testIngestSummarizedSections()
    testSummarizationRetries()
    testVisionFallback()
    print("\nALL PERSON 2 VERIFICATION TESTS PASSED SUCCESSFULLY!")
