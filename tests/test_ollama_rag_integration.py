"""Tests for RAG integration in ollama_client.py"""
import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


def _make_httpx_mock(tokens):
    """Create a properly structured httpx mock for streaming responses."""
    lines = []
    for i, token in enumerate(tokens):
        is_last = i == len(tokens) - 1
        lines.append(json.dumps({"message": {"content": token}, "done": is_last}))

    async def aiter_lines():
        for line in lines:
            yield line

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.aiter_lines = aiter_lines
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    mock_client = MagicMock()
    mock_client.stream = MagicMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    return mock_client


class TestChatStreamWithRag:
    @pytest.mark.asyncio
    async def test_rag_context_injected_when_available(self):
        """When RAG returns context, it should be included in system prompt."""
        from App.services.ollama_client import chat_stream_with_rag

        mock_context = "참고 음악 지식: Pop song at 120 BPM"
        mock_client = _make_httpx_mock(["Hello", " world"])

        with patch(
            "App.services.youtube_learning.rag_retriever.retrieve_context",
            new_callable=AsyncMock,
            return_value=mock_context,
        ) as mock_retrieve, patch(
            "httpx.AsyncClient",
            return_value=mock_client,
        ):
            tokens = []
            async for token in chat_stream_with_rag("test message", []):
                tokens.append(token)

            assert tokens == ["Hello", " world"]
            mock_retrieve.assert_called_once_with("test message")

            # Verify system prompt includes RAG context
            call_args = mock_client.stream.call_args
            payload = call_args[1]["json"]
            system_msg = payload["messages"][0]["content"]
            assert "참고 음악 지식" in system_msg

    @pytest.mark.asyncio
    async def test_rag_failure_falls_back(self):
        """When RAG fails, should use plain system prompt."""
        from App.services.ollama_client import chat_stream_with_rag, SYSTEM_PROMPT

        mock_client = _make_httpx_mock(["OK"])

        with patch(
            "App.services.youtube_learning.rag_retriever.retrieve_context",
            new_callable=AsyncMock,
            side_effect=Exception("ChromaDB crashed"),
        ), patch(
            "httpx.AsyncClient",
            return_value=mock_client,
        ):
            tokens = []
            async for token in chat_stream_with_rag("test", []):
                tokens.append(token)

            assert tokens == ["OK"]

            call_args = mock_client.stream.call_args
            payload = call_args[1]["json"]
            system_msg = payload["messages"][0]["content"]
            assert system_msg == SYSTEM_PROMPT

    @pytest.mark.asyncio
    async def test_empty_rag_context_uses_plain_prompt(self):
        """When RAG returns empty string, should use plain system prompt."""
        from App.services.ollama_client import chat_stream_with_rag, SYSTEM_PROMPT

        mock_client = _make_httpx_mock(["hi"])

        with patch(
            "App.services.youtube_learning.rag_retriever.retrieve_context",
            new_callable=AsyncMock,
            return_value="",
        ), patch(
            "httpx.AsyncClient",
            return_value=mock_client,
        ):
            tokens = []
            async for token in chat_stream_with_rag("test", []):
                tokens.append(token)

            call_args = mock_client.stream.call_args
            payload = call_args[1]["json"]
            system_msg = payload["messages"][0]["content"]
            assert system_msg == SYSTEM_PROMPT

    @pytest.mark.asyncio
    async def test_history_preserved_in_messages(self):
        """Chat history should be included between system prompt and user message."""
        from App.services.ollama_client import chat_stream_with_rag

        mock_client = _make_httpx_mock(["response"])

        history = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ]

        with patch(
            "App.services.youtube_learning.rag_retriever.retrieve_context",
            new_callable=AsyncMock,
            return_value="",
        ), patch(
            "httpx.AsyncClient",
            return_value=mock_client,
        ):
            tokens = []
            async for token in chat_stream_with_rag("new message", history):
                tokens.append(token)

            call_args = mock_client.stream.call_args
            payload = call_args[1]["json"]
            messages = payload["messages"]

            assert messages[0]["role"] == "system"
            assert messages[1]["role"] == "user"
            assert messages[1]["content"] == "hello"
            assert messages[2]["role"] == "assistant"
            assert messages[2]["content"] == "hi there"
            assert messages[3]["role"] == "user"
            assert messages[3]["content"] == "new message"
