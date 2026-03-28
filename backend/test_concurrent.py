"""
Test: send two commands back-to-back and verify concurrent execution.
  1) "Find cheap flights from PHX to SF"
  2) After 5s -> "Find top 10 AI news"

Monitors WebSocket events to confirm:
  - Both tasks get accepted
  - Agents get unique global_index values (no collision)
  - Both tasks initiate without blocking each other
"""

import asyncio
import json
import aiohttp

BASE = "http://127.0.0.1:8080"
WS_URL = "ws://127.0.0.1:8080/ws"

TASK_1 = "Find cheap flights from PHX to SF"
TASK_2 = "Find top 10 AI news"

TIMEOUT = 600


async def submit_task(task: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE}/api/v1/tasks/submit",
            json={"task": task},
        ) as resp:
            data = await resp.json()
            print(f"  > Submitted: {task!r}  task_id={data.get('task_id')}")
            return data


async def run_test():
    global_indices: list[int] = []
    task_ids: list[str] = []
    tasks_accepted = 0
    agents_spawned = 0
    tasks_completed = 0
    stop = asyncio.Event()

    async def ws_listener():
        nonlocal tasks_accepted, agents_spawned, tasks_completed
        async with aiohttp.ClientSession() as session:
            ws = await session.ws_connect(WS_URL, heartbeat=30)
            print("[WS] Listener connected\n")
            async for msg in ws:
                if stop.is_set():
                    break
                if msg.type != aiohttp.WSMsgType.TEXT:
                    if msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        print(f"[WS] Lost: {msg.type}")
                        break
                    continue

                evt = json.loads(msg.data)
                etype = evt.get("type", "")

                if etype in ("PING", "TABS_UPDATE"):
                    continue

                d = evt.get("data", {})

                if etype == "TASK_ACCEPTED":
                    tasks_accepted += 1
                    print(f"[TASK_ACCEPTED] task_id={d.get('task_id')}  agents={d.get('subtask_count')}")

                elif etype == "AGENT_SPAWNED":
                    agents_spawned += 1
                    gidx = d.get("global_index", "?")
                    global_indices.append(gidx)
                    print(f"[AGENT_SPAWNED] global#{gidx}  task={d.get('task_id')}  agent={d.get('agent_id')}")
                    print(f"                desc: {d.get('task_description', '')[:60]}")

                elif etype == "AGENT_STATUS":
                    print(f"[AGENT_STATUS]  {d.get('agent_id')}  -> {d.get('status')}  step={d.get('step', 0)}")

                elif etype == "AGENT_LOG":
                    print(f"[AGENT_LOG]     {d.get('agent_id')}: {d.get('message', '')[:80]}")

                elif etype == "AGENT_COMPLETED":
                    print(f"[AGENT_DONE]    {d.get('agent_id')}  steps={d.get('steps_taken')}")
                    print(f"                result: {d.get('result', '')[:100]}...")

                elif etype == "AGENT_FAILED":
                    print(f"[AGENT_FAIL]    {d.get('agent_id')}: {d.get('error', '')[:120]}")

                elif etype == "TASK_COMPLETE":
                    tasks_completed += 1
                    n = len(d.get("agent_results", []))
                    print(f"\n[TASK_COMPLETE] task_id={d.get('task_id')}  agents={n}")
                    print(f"                result: {d.get('final_result', '')[:120]}...")
                    if tasks_completed >= 2:
                        print("\n[OK] Both tasks completed!")
                        stop.set()
                        break
                else:
                    print(f"[{etype}] ...")

            await ws.close()

    listener_task = asyncio.create_task(ws_listener())
    await asyncio.sleep(1)

    print("=== Sending Task 1 ===")
    r1 = await submit_task(TASK_1)
    task_ids.append(r1["task_id"])

    print(f"\n... waiting 5 seconds before Task 2 ...\n")
    await asyncio.sleep(5)

    print("=== Sending Task 2 ===")
    r2 = await submit_task(TASK_2)
    task_ids.append(r2["task_id"])

    print(f"\n--- Monitoring events (timeout {TIMEOUT}s) ---\n")

    try:
        await asyncio.wait_for(stop.wait(), timeout=TIMEOUT)
    except asyncio.TimeoutError:
        print(f"\n[TIMEOUT] after {TIMEOUT}s")
        stop.set()

    listener_task.cancel()
    try:
        await listener_task
    except asyncio.CancelledError:
        pass

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Tasks accepted:   {tasks_accepted}")
    print(f"Agents spawned:   {agents_spawned}")
    print(f"Tasks completed:  {tasks_completed}")
    print(f"Task IDs:         {task_ids}")
    print(f"Global indices:   {global_indices}")

    unique_indices = len(set(global_indices))
    if unique_indices == len(global_indices) and len(global_indices) > 0:
        print(f"\n[PASS] All {unique_indices} agent(s) have unique global indices")
    elif len(global_indices) == 0:
        print("\n[FAIL] No agents were spawned")
    else:
        print(f"\n[FAIL] Global index collision! {global_indices}")

    if tasks_accepted >= 2:
        print("[PASS] Both tasks were accepted concurrently")
    else:
        print(f"[FAIL] Only {tasks_accepted} task(s) accepted")


if __name__ == "__main__":
    asyncio.run(run_test())
