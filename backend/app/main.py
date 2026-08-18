from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import chat_router, document_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.pdfUploadDir.mkdir(parents=True, exist_ok=True)
    settings.chromaPersistDir.mkdir(parents=True, exist_ok=True)
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
