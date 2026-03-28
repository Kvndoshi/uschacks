"""Quick test: verify MiniMax API key works."""
import asyncio, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from dotenv import load_dotenv
load_dotenv()

# Ensure we can import from backend correctly if this is run from backend dir
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import MINIMAX_API_KEY, MINIMAX_BASE_URL
from services.minimax_client import minimax_chat, minimax_chat_stream

async def test_chat():
    print(f"Key: {MINIMAX_API_KEY[:4]}...{MINIMAX_API_KEY[-4:]}" if MINIMAX_API_KEY else "No Key Found")
    print(f"Base URL: {MINIMAX_BASE_URL}")
    print()

    print("--- Testing minimax_chat ---")
    messages = [{"role": "user", "content": "Say hello in one sentence."}]
    try:
        res = await minimax_chat(messages, model="minimax-m2.7", max_tokens=50)
        print(f"OK: {res}")
    except Exception as e:
        print(f"FAILED chat: {e}")

    print()
    print("--- Testing minimax_chat_stream ---")
    try:
        print("OK Stream:", end=" ")
        async for chunk in minimax_chat_stream(messages, model="minimax-m2.7", max_tokens=50):
            print(chunk, end="", flush=True)
        print()
    except Exception as e:
        print(f"FAILED stream: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat())
