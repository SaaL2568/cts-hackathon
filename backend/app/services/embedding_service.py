from typing import Optional

from sentence_transformers import SentenceTransformer

from ..config import settings


class EmbeddingService:
    def __init__(self, modelName: str = settings.embeddingModelName):
        self.modelName = modelName
        self._model: Optional[SentenceTransformer] = None

    def _loadModel(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.modelName)
        return self._model

    def embedTexts(self, texts: list[str]) -> list[list[float]]:
        model = self._loadModel()
        vectors = model.encode(texts, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]

    def embedText(self, text: str) -> list[float]:
        return self.embedTexts([text])[0]
