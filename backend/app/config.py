from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

# Up-front constants (SCREAMING_SNAKE_CASE). These are the defaults; env vars
# in .env can override them through Settings below.
MAX_CHUNK_TOKENS = 512
CHUNK_OVERLAP = 50
TOP_K_RESULTS = 5
CONFIDENCE_THRESHOLD = 0.7
MAX_HISTORY_TURNS = 10
QUERY_INSTRUCTION_PREFIX = "Represent this sentence for searching relevant passages: "
OPENFDA_LABEL_URL = "https://api.fda.gov/drug/label.json"
DAILYMED_PDF_URL = "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    appName: str = Field(
        default="cts-drug-chatbot",
        validation_alias=AliasChoices("APP_NAME", "appName"),
    )
    debug: bool = Field(
        default=True,
        validation_alias=AliasChoices("DEBUG", "debug"),
    )
    apiPrefix: str = Field(
        default="/api/v1",
        validation_alias=AliasChoices("API_PREFIX", "apiPrefix"),
    )
    corsOriginsRaw: str = Field(
        default="http://localhost:3000",
        validation_alias=AliasChoices("CORS_ORIGINS", "corsOrigins"),
    )

    maxChunkTokens: int = Field(
        default=MAX_CHUNK_TOKENS,
        validation_alias=AliasChoices("MAX_CHUNK_TOKENS", "maxChunkTokens"),
    )
    chunkOverlap: int = Field(
        default=CHUNK_OVERLAP,
        validation_alias=AliasChoices("CHUNK_OVERLAP", "chunkOverlap"),
    )
    topKResults: int = Field(
        default=TOP_K_RESULTS,
        validation_alias=AliasChoices("TOP_K_RESULTS", "topKResults"),
    )
    confidenceThreshold: float = Field(
        default=CONFIDENCE_THRESHOLD,
        validation_alias=AliasChoices("CONFIDENCE_THRESHOLD", "confidenceThreshold"),
    )
    maxHistoryTurns: int = Field(
        default=MAX_HISTORY_TURNS,
        validation_alias=AliasChoices("MAX_HISTORY_TURNS", "maxHistoryTurns"),
    )
    queryInstructionPrefix: str = Field(
        default=QUERY_INSTRUCTION_PREFIX,
        validation_alias=AliasChoices(
            "QUERY_INSTRUCTION_PREFIX", "queryInstructionPrefix"
        ),
    )

    pdfUploadDir: Path = Field(
        default=BASE_DIR / "data" / "pdfs",
        validation_alias=AliasChoices("PDF_UPLOAD_DIR", "pdfUploadDir"),
    )
    chromaPersistDir: Path = Field(
        default=BASE_DIR / "data" / "vector_store",
        validation_alias=AliasChoices("CHROMA_PERSIST_DIR", "chromaPersistDir"),
    )
    sessionPersistDir: Path = Field(
        default=BASE_DIR / "data" / "sessions",
        validation_alias=AliasChoices("SESSION_PERSIST_DIR", "sessionPersistDir"),
    )
    chromaCollectionName: str = Field(
        default="drug_label_chunks",
        validation_alias=AliasChoices("CHROMA_COLLECTION_NAME", "chromaCollectionName"),
    )

    embeddingModelName: str = Field(
        default="BAAI/bge-small-en-v1.5",
        validation_alias=AliasChoices("EMBEDDING_MODEL_NAME", "embeddingModelName"),
    )

    ollamaBaseUrl: str = Field(
        default="http://localhost:11434",
        validation_alias=AliasChoices("OLLAMA_BASE_URL", "ollamaBaseUrl"),
    )
    ollamaModel: str = Field(
        default="llama3.1",
        validation_alias=AliasChoices("OLLAMA_MODEL", "ollamaModel"),
    )
    ollamaTimeoutSeconds: int = Field(
        default=120,
        validation_alias=AliasChoices("OLLAMA_TIMEOUT_SECONDS", "ollamaTimeoutSeconds"),
    )

    publicLookupEnabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("PUBLIC_LOOKUP_ENABLED", "publicLookupEnabled"),
    )
    publicLookupTimeoutSeconds: int = Field(
        default=180,
        validation_alias=AliasChoices(
            "PUBLIC_LOOKUP_TIMEOUT_SECONDS", "publicLookupTimeoutSeconds"
        ),
    )
    openfdaLabelUrl: str = Field(
        default=OPENFDA_LABEL_URL,
        validation_alias=AliasChoices("OPENFDA_LABEL_URL", "openfdaLabelUrl"),
    )
    dailymedPdfUrl: str = Field(
        default=DAILYMED_PDF_URL,
        validation_alias=AliasChoices("DAILYMED_PDF_URL", "dailymedPdfUrl"),
    )

    @property
    def corsOrigins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.corsOriginsRaw.split(",")
            if origin.strip()
        ]


settings = Settings()
