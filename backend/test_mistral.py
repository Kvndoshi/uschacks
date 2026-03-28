"""Quick test: verify Mistral API key works."""
import asyncio, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from dotenv import load_dotenv
load_dotenv()

from config import MISTRAL_API_KEY, MISTRAL_BASE_URL, QUEEN_MODEL, WORKER_MODEL

async def test_chat():
    from openai import AsyncOpenAI

    print(f"Key: {MISTRAL_API_KEY[:8]}...{MISTRAL_API_KEY[-4:]}")
    print(f"Base URL: {MISTRAL_BASE_URL}")
    print(f"Queen model: {QUEEN_MODEL}")
    print(f"Worker model: {WORKER_MODEL}")
    print()

    client = AsyncOpenAI(api_key=MISTRAL_API_KEY, base_url=MISTRAL_BASE_URL)

    print("--- Testing with queen model ---")
    try:
        resp = await client.chat.completions.create(
            model=QUEEN_MODEL,
            messages=[{"role": "user", "content": "Say hello in one sentence."}],
            max_tokens=50,
        )
        print(f"OK: {resp.choices[0].message.content}")
    except Exception as e:
        print(f"FAILED: {e}")

    print()
    print("--- Testing with worker model ---")
    try:
        resp = await client.chat.completions.create(
            model=WORKER_MODEL,
            messages=[{"role": "user", "content": "Say hello in one sentence."}],
            max_tokens=50,
        )
        print(f"OK: {resp.choices[0].message.content}")
    except Exception as e:
        print(f"FAILED: {e}")

    # Also test with the Mistral native endpoint (not /v1)
    print()
    print("--- Testing Mistral native endpoint (no /v1 suffix) ---")
    client2 = AsyncOpenAI(api_key=MISTRAL_API_KEY, base_url="https://api.mistral.ai")
    try:
        resp = await client2.chat.completions.create(
            model=WORKER_MODEL,
            messages=[{"role": "user", "content": "Say hello in one sentence."}],
            max_tokens=50,
        )
        print(f"OK: {resp.choices[0].message.content}")
    except Exception as e:
        print(f"FAILED: {e}")

    # Test with /v1 explicitly
    print()
    print("--- Testing with Bearer token header ---")
    client3 = AsyncOpenAI(
        api_key=MISTRAL_API_KEY,
        base_url="https://api.mistral.ai/v1",
    )
    try:
        resp = await client3.chat.completions.create(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": "Say hi"}],
            max_tokens=20,
        )
        print(f"OK: {resp.choices[0].message.content}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat())
