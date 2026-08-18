import threading

import chromadb

from ..config import settings

_collection = None
_lock = threading.Lock()


def getCollection():
    global _collection
    if _collection is None:
        with _lock:
            if _collection is None:
                client = chromadb.PersistentClient(path=str(settings.chromaPersistDir))
                _collection = client.get_or_create_collection(
                    name=settings.chromaCollectionName,
                    metadata={"hnsw:space": "cosine"},
                )
    return _collection


def docExists(docName: str) -> bool:
    """Return True if at least one chunk with the given docName exists."""
    collection = getCollection()
    # Guard: ChromaDB may raise on `where` filter against an empty collection.
    if collection.count() == 0:
        return False
    result = collection.get(where={"docName": docName}, limit=1)
    return len(result.get("ids") or []) > 0
