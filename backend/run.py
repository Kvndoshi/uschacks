"""
Start the Mind backend with the correct asyncio policy on Windows.

Run this instead of `uvicorn main:app` so the event loop policy is set before
any other code runs.

IMPORTANT: reload=False is required on Windows. With reload=True, uvicorn
spawns a child process whose asyncio_setup() forcibly sets
WindowsSelectorEventLoopPolicy, overriding our ProactorEventLoop.
Without ProactorEventLoop, browser-use cannot create subprocesses and ALL
agents fail with NotImplementedError.
"""
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(__import__("os").getenv("PORT", "8081")),
        reload=False,
        log_level="info",
    )
