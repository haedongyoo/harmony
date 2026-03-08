import logging
from typing import Dict, List
from pathlib import Path
from ...internal.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_client = None
_collection = None


def _get_collection():
    """Lazy-init ChromaDB client and collection (singleton)."""
    global _client, _collection
    if _collection is None:
        import chromadb
        from chromadb.utils import embedding_functions

        persist_dir = Path(settings.chromadb_path)
        persist_dir.mkdir(parents=True, exist_ok=True)

        _client = chromadb.PersistentClient(path=str(persist_dir))

        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model
        )

        _collection = _client.get_or_create_collection(
            name=settings.chromadb_collection_name,
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )

        logger.info(
            f"ChromaDB collection '{settings.chromadb_collection_name}' initialized "
            f"with {_collection.count()} documents"
        )

    return _collection


def index_document(doc_id: str, document: str, metadata: Dict) -> str:
    """Add a single document to ChromaDB. Returns the document ID."""
    collection = _get_collection()
    chroma_id = f"yt_{metadata.get('video_id', doc_id)}"

    collection.upsert(
        ids=[chroma_id],
        documents=[document],
        metadatas=[metadata],
    )

    logger.debug(f"Indexed document: {chroma_id}")
    return chroma_id


def index_batch(
    doc_ids: List[str],
    documents: List[str],
    metadatas: List[Dict],
) -> List[str]:
    """Batch-index multiple documents."""
    collection = _get_collection()
    chroma_ids = [f"yt_{mid}" for mid in doc_ids]

    batch_size = 500
    for i in range(0, len(documents), batch_size):
        end = min(i + batch_size, len(documents))
        collection.upsert(
            ids=chroma_ids[i:end],
            documents=documents[i:end],
            metadatas=metadatas[i:end],
        )

    logger.info(f"Batch-indexed {len(documents)} documents")
    return chroma_ids


def get_collection_stats() -> Dict:
    """Return stats about the ChromaDB collection."""
    try:
        collection = _get_collection()
        return {
            "total_documents": collection.count(),
            "collection_name": settings.chromadb_collection_name,
            "embedding_model": settings.embedding_model,
        }
    except Exception as e:
        return {"error": str(e)}


def delete_document(doc_id: str) -> None:
    """Remove a document from ChromaDB."""
    collection = _get_collection()
    collection.delete(ids=[doc_id])
