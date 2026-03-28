"""Test: run the Playwright agent directly to see the exact error."""
import asyncio
import logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s [%(name)s] %(message)s")

async def main():
    from services.playwright_agent import run_playwright_agent

    async def on_step(state, output, step):
        url = getattr(state, 'url', '?')
        print(f"\n  STEP {step}: {output[:120]}")
        print(f"  URL: {url}")

    print("=== Direct Playwright Agent Test ===\n")
    print("Connecting to Chrome CDP at http://localhost:9222...")

    try:
        result = await run_playwright_agent(
            task="Report the title of the current page. Say ACTION: done with the title as VALUE.",
            cdp_url="http://localhost:9222",
            cdp_target_id=None,
            start_url=None,
            on_step_callback=on_step,
        )
        print(f"\n  RESULT: {result}")
    except Exception as e:
        print(f"\n  FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(main())
