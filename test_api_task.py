"""Test: submit a task via the API and poll for results."""
import urllib.request, json, time

BACKEND = "http://localhost:8080"

# Get tab
r = urllib.request.urlopen(f"{BACKEND}/api/v1/tabs/status", timeout=3)
d = json.loads(r.read())
tids = list(d.get("targets", {}).keys())
print("Available tabs:", tids)

if not tids:
    print("No tabs! Open a tab in Chrome.")
    exit(1)

# Submit task via API
body = json.dumps({
    "instructions": [{"tab_id": tids[0], "instruction": "Navigate to https://news.ycombinator.com and report the page title"}],
    "global_task": "",
}).encode()
req = urllib.request.Request(f"{BACKEND}/api/v1/tabs/execute", data=body, headers={"Content-Type": "application/json"})
r = urllib.request.urlopen(req, timeout=10)
print("Submit response:", r.read().decode())

# Wait and poll agent logs
print("Waiting for agent to run...")
for i in range(20):
    time.sleep(3)
    try:
        r2 = urllib.request.urlopen(f"{BACKEND}/api/v1/tabs/diagnostic", timeout=5)
        diag = json.loads(r2.read())
        logs = diag.get("checks", {}).get("agent_logs", {})
        agents = diag.get("checks", {}).get("agents", {})
        active = agents.get("active", [])
        total_logs = sum(logs.values())
        print(f"  [{(i+1)*3}s] active={len(active)} total_log_entries={total_logs}")

        if not active and total_logs > 0:
            print("\nAgent finished! Fetching logs...")
            for aid, count in logs.items():
                if count > 0:
                    r3 = urllib.request.urlopen(f"{BACKEND}/api/v1/agents/{aid}/logs", timeout=3)
                    al = json.loads(r3.read())
                    print(f"\n  Agent: {aid}")
                    for entry in al.get("logs", []):
                        step = entry.get("step", "?")
                        msg = entry.get("message", "")[:120]
                        url = entry.get("url", "")
                        print(f"    Step {step}: {msg}")
                        if url:
                            print(f"           URL: {url}")
            break
    except Exception as e:
        print(f"  [{(i+1)*3}s] poll error: {e}")
else:
    print("\nTimeout — agent didn't finish in 60s")
