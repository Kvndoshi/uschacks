import pytest
from unittest.mock import patch, AsyncMock
import sys
import os

# Add backend to path if needed or assume pytest runs from root
from backend.services.minimax_client import minimax_chat, minimax_chat_stream

@pytest.mark.asyncio
async def test_minimax_chat():
    messages = [{"role": "user", "content": "Hello"}]
    
    with patch("backend.services.minimax_client.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock(message=AsyncMock(content="Hi there!"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        result = await minimax_chat(messages, model="minimax-m2.7")
        
        assert result == "Hi there!"
        mock_client.chat.completions.create.assert_called_once_with(
            model="minimax-m2.7",
            messages=messages,
            temperature=0.5,
            max_tokens=1024
        )

@pytest.mark.asyncio
async def test_minimax_chat_stream():
    messages = [{"role": "user", "content": "Hello"}]
    
    with patch("backend.services.minimax_client.get_client") as mock_get_client:
        mock_client = AsyncMock()
        
        # Mock streaming response
        async def mock_stream():
            class MockChoice:
                def __init__(self, content):
                    self.delta = AsyncMock(content=content)
            
            class MockChunk:
                def __init__(self, content):
                    self.choices = [MockChoice(content)]
                    
            yield MockChunk("Hi")
            yield MockChunk(" there")
            yield MockChunk("!")
            
        mock_client.chat.completions.create.return_value = mock_stream()
        mock_get_client.return_value = mock_client
        
        chunks = []
        async for chunk in minimax_chat_stream(messages, model="minimax-m2.7"):
            chunks.append(chunk)
            
        assert chunks == ["Hi", " there", "!"]
        mock_client.chat.completions.create.assert_called_once_with(
            model="minimax-m2.7",
            messages=messages,
            temperature=0.5,
            max_tokens=1024,
            stream=True
        )
