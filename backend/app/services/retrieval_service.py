from ..config import settings
from ..errors import RetrievalError
from ..models.schemas import RetrievedChunk
from .embedding_service import EmbeddingService
from .vector_store_client import getCollection


class RetrievalService:
    def __init__(self, embeddingService: EmbeddingService):
        self.embeddingService = embeddingService

    def retrieveRelevantChunks(
        self, query: str, topK: int = settings.topKResults
    ) -> list[RetrievedChunk]:
        try:
            collection = getCollection()
            if collection.count() == 0:
                return []

            prefixedQuery = f"{settings.queryInstructionPrefix}{query}"
            queryEmbedding = self.embeddingService.embedText(prefixedQuery)
            nResults = min(max(1, topK), collection.count())
            result = collection.query(
                query_embeddings=[queryEmbedding],
                n_results=nResults,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            raise RetrievalError(f"Vector store query failed: {exc}") from exc

        chunkIds = (result.get("ids") or [[]])[0]
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        retrieved: list[RetrievedChunk] = []
        for chunkId, text, metadata, distance in zip(
            chunkIds, documents, metadatas, distances
        ):
            if text is None or metadata is None:
                continue
            score = 1.0 - float(distance)
            retrieved.append(
                RetrievedChunk(
                    chunkId=str(chunkId),
                    docName=str(metadata.get("docName") or "unknown"),
                    pageNum=int(metadata.get("pageNum") or 0),
                    section=metadata.get("section") or None,
                    text=str(text),
                    score=score,
                )
            )
        retrieved.sort(key=lambda chunk: chunk.score, reverse=True)
        return retrieved
