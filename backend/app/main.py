import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .dependencies import documentIngestionService
from .routers import chat_router, document_router
from .services.vector_store_client import docExists

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.authEnabled and not settings.apiAuthSecret.strip():
        raise RuntimeError(
            "AUTH_ENABLED is True but API_AUTH_SECRET is empty. "
            "Set API_AUTH_SECRET in .env or disable AUTH_ENABLED."
        )

    settings.pdfUploadDir.mkdir(parents=True, exist_ok=True)
    settings.chromaPersistDir.mkdir(parents=True, exist_ok=True)
    settings.sessionPersistDir.mkdir(parents=True, exist_ok=True)

    # Auto-ingest all PDFs found in the data/pdfs directory
    pdfDir = settings.pdfUploadDir
    pdfFiles = sorted(pdfDir.glob("*.pdf"))
    logger.info("Found %d PDF(s) in %s", len(pdfFiles), pdfDir)

    for pdfPath in pdfFiles:
        docName = pdfPath.stem
        if docExists(docName):
            logger.info("  [SKIP] %s — already indexed", docName)
            continue
        try:
            chunkCount, pagesProcessed = documentIngestionService.ingestDocument(
                str(pdfPath), docName
            )
            logger.info(
                "  [OK]   %s — %d chunks, %d pages", docName, chunkCount, pagesProcessed
            )
        except Exception as exc:
            logger.error("  [FAIL] %s — %s", docName, exc)

    logger.info("Startup ingestion complete.")
    yield


app = FastAPI(
    title=settings.appName,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.corsOrigins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(document_router.router, prefix=settings.apiPrefix)
app.include_router(chat_router.router, prefix=settings.apiPrefix)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

