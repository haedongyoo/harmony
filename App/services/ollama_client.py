import httpx
from typing import AsyncGenerator, List, Dict
from ..internal.config import get_settings

settings = get_settings()

SYSTEM_PROMPT = (
    "당신은 음악 제작 전문가 AI입니다. "
    "사용자가 원하는 음악을 구체적인 프롬프트로 변환해 주세요. "
    "음악 프롬프트를 제안할 때는 반드시 [MUSIC_PROMPT: <프롬프트>] 형식으로 포함하세요."
)


async def chat_stream(
    message: str,
    history: List[Dict],
) -> AsyncGenerator[str, None]:
    """Ollama /api/chat 에 스트리밍 요청. 토큰 단위로 yield."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    url = f"{settings.ollama_base_url}/api/chat"
    payload = {
        "model": settings.ollama_chat_model,
        "messages": messages,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", url, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line:
                    continue
                import json
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                token = data.get("message", {}).get("content", "")
                if token:
                    yield token
                if data.get("done"):
                    break


async def chat_stream_with_rag(
    message: str,
    history: List[Dict],
) -> AsyncGenerator[str, None]:
    """
    RAG-enhanced version of chat_stream.
    Retrieves relevant music knowledge from ChromaDB and injects into system prompt.
    Falls back to regular system prompt on any RAG failure.
    """
    rag_context = ""
    try:
        from .youtube_learning.rag_retriever import retrieve_context
        rag_context = await retrieve_context(message)
    except Exception:
        pass

    if rag_context:
        enhanced_system = (
            f"{SYSTEM_PROMPT}\n\n"
            f"--- 참고 음악 지식 ---\n"
            f"{rag_context}\n"
            f"--- 참고 끝 ---"
        )
    else:
        enhanced_system = SYSTEM_PROMPT

    messages = [{"role": "system", "content": enhanced_system}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    url = f"{settings.ollama_base_url}/api/chat"
    payload = {
        "model": settings.ollama_chat_model,
        "messages": messages,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", url, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line:
                    continue
                import json
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                token = data.get("message", {}).get("content", "")
                if token:
                    yield token
                if data.get("done"):
                    break


async def complete(prompt: str) -> str:
    """단순 completion (스트리밍 없음). 트렌드 분석 등 내부 호출용."""
    url = f"{settings.ollama_base_url}/api/generate"
    payload = {
        "model": settings.ollama_chat_model,
        "prompt": prompt,
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json().get("response", "")
