import logging
from typing import List, Dict
from ...internal.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


async def retrieve_context(query: str, top_k: int = None) -> str:
    """
    Search ChromaDB for documents relevant to the query.
    Returns formatted context string for Ollama system prompt injection.
    Returns empty string if RAG is disabled or no results found.
    """
    if not settings.rag_enabled:
        return ""

    top_k = top_k or settings.rag_top_k

    try:
        from .rag_indexer import _get_collection
        collection = _get_collection()

        if collection.count() == 0:
            return ""

        results = collection.query(
            query_texts=[query],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        if not results or not results["documents"] or not results["documents"][0]:
            return ""

        documents = results["documents"][0]
        distances = results["distances"][0] if results.get("distances") else []

        # Filter out low-relevance results (cosine distance > 0.8)
        relevant_docs = []
        for i, doc in enumerate(documents):
            distance = distances[i] if i < len(distances) else 1.0
            if distance < 0.8:
                relevant_docs.append(doc)

        if not relevant_docs:
            return ""

        context_parts = [
            "다음은 현재 음악 트렌드와 관련된 참고 정보입니다 (YouTube 음악 분석 데이터):"
        ]
        for i, doc in enumerate(relevant_docs, 1):
            context_parts.append(f"\n[참고 {i}]\n{doc}")

        context_parts.append(
            "\n위 정보를 참고하여 사용자의 질문에 답해주세요. "
            "단, 참고 정보가 질문과 관련이 없다면 무시하세요."
        )

        return "\n".join(context_parts)

    except Exception as e:
        logger.warning(f"RAG retrieval failed: {e}")
        return ""


async def retrieve_for_prompt_enhancement(
    prompt: str, genre: str = None, top_k: int = 3
) -> List[Dict]:
    """
    Retrieve music features relevant to a generation prompt.
    Returns list of metadata dicts for prompt enhancement.
    """
    if not settings.rag_enabled:
        return []

    try:
        from .rag_indexer import _get_collection
        collection = _get_collection()

        if collection.count() == 0:
            return []

        query = f"{genre} music: {prompt}" if genre else prompt
        where_filter = {"genre": genre} if genre else None

        results = collection.query(
            query_texts=[query],
            n_results=min(top_k, collection.count()),
            where=where_filter,
            include=["metadatas", "distances"],
        )

        if not results or not results["metadatas"] or not results["metadatas"][0]:
            return []

        return [
            meta for meta, dist in zip(
                results["metadatas"][0],
                results["distances"][0] if results.get("distances") else [1.0] * len(results["metadatas"][0])
            )
            if dist < 0.7
        ]

    except Exception as e:
        logger.warning(f"RAG prompt retrieval failed: {e}")
        return []
