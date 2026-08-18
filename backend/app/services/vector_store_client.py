import chromadb

from ..config import settings

_collection = None


def getCollection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=str(settings.chromaPersistDir))
        _collection = client.get_or_create_collection(
            name=settings.chromaCollectionName,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection
