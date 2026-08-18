import asyncio
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..config import settings
from ..dependencies import documentIngestionService
from ..errors import IngestionError
from ..models.schemas import ListDocumentsResponse, UploadDocumentResponse
from ..services.vector_store_client import listDocNames

router = APIRouter(tags=["documents"])


@router.get("/listDocuments", response_model=ListDocumentsResponse)
def listDocuments() -> ListDocumentsResponse:
    names = listDocNames()
    return ListDocumentsResponse(documents=names)


@router.post("/uploadDocument", response_model=UploadDocumentResponse)
async def uploadDocument(
    file: UploadFile = File(...),
    docName: Optional[str] = Form(default=None),
) -> UploadDocumentResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    safeFilename = Path(file.filename).name
    settings.pdfUploadDir.mkdir(parents=True, exist_ok=True)
    destination = settings.pdfUploadDir / safeFilename

    try:
        content = await file.read()
        destination.write_bytes(content)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {exc}") from exc

    name = docName.strip() if docName and docName.strip() else Path(safeFilename).stem
    try:
        chunkCount, pagesProcessed = await asyncio.get_running_loop().run_in_executor(
            None, documentIngestionService.ingestDocument, str(destination), name
        )
    except IngestionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {exc}") from exc

    return UploadDocumentResponse(
        docName=name,
        chunksIndexed=chunkCount,
        pagesProcessed=pagesProcessed,
    )
