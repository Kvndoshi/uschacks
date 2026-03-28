"""
End-to-end diagnostic test for the Mindd pipeline.
Run: python test_pipeline.py

Tests:
 1. Backend health
 2. Chrome CDP HTTP connectivity
 3. Chrome CDP WebSocket connectivity (origin header)
 4. Tab scan & listing
 5. Screenshot capture
 6. Mistral API key present
 7. WebSocket connection
 8. Agent task submission (dry run)
 9. Diagnostic endpoint
"""
import asyncio
import json
import sys
import urllib.request
import urllib.error

BACKEND = "http://localhost:8080"
CDP = "http://localhost:9222"

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
WARN = "\033[93mWARN\033[0m"
results = []


def check(name: str, ok: bool, detail: str = ""):
    tag = PASS if ok else FAIL
    results.append((name, ok))
    suffix = f" — {detail}" if detail else ""
    print(f"  [{tag}] {name}{suffix}")


def http_get(url, timeout=5):
    r = urllib.request.urlopen(url, timeout=timeout)
    return json.loads(r.read())


def http_post(url, body, timeout=10):
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=timeout)
    return json.loads(r.read())


def main():
    print("\n=== Mindd Pipeline Diagnostic ===\n")

    # 1. Backend health
    print("[1/9] Backend Health")
    try:
        d = http_get(f"{BACKEND}/health")
        check("Backend reachable", True, f"WS clients: {d.get('connections', 0)}")
    except Exception as e:
        check("Backend reachable", False, str(e))
        print("\n  FATAL: Backend not running. Start with: python run.py")
        return

    # 2. Chrome CDP HTTP
    print("\n[2/9] Chrome CDP HTTP")
    targets = []
    try:
        targets = http_get(f"{CDP}/json")
        check("CDP HTTP (/json)", True, f"{len(targets)} targets")
    except Exception as e:
        check("CDP HTTP (/json)", False, str(e))
        print(f"\n  ACTION: Launch Chrome with:")
        print(f"    chrome --remote-debugging-port=9222 --remote-allow-origins=*")

    # 3. Chrome CDP WebSocket
    print("\n[3/9] Chrome CDP WebSocket")
    ws_ok = False
    if targets:
        ws_url = targets[0].get("webSocketDebuggerUrl", "")
        if ws_url:
            try:
                import websocket
                ws = websocket.create_connection(ws_url, timeout=3, origin="http://localhost:9222")
                ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": "navigator.userAgent"}}))
                raw = ws.recv()
                data = json.loads(raw)
                if data.get("id") == 1 and not data.get("error"):
                    ua = data.get("result", {}).get("result", {}).get("value", "?")
                    check("CDP WebSocket", True, f"UA: {ua[:50]}")
                    ws_ok = True
                else:
                    check("CDP WebSocket", False, f"CDP error: {data.get('error')}")
                ws.close()
            except Exception as e:
                err = str(e)
                if "403" in err:
                    check("CDP WebSocket", False, "403 Forbidden — Chrome needs --remote-allow-origins=*")
                else:
                    check("CDP WebSocket", False, err[:80])
        else:
            check("CDP WebSocket", False, "No webSocketDebuggerUrl in targets")
    else:
        check("CDP WebSocket", False, "No CDP targets available")

    # 4. Tab scan
    print("\n[4/9] Tab Scan")
    try:
        d = http_get(f"{BACKEND}/api/v1/tabs/status")
        tab_count = d.get("tab_count", 0)
        cdp_connected = d.get("cdp_connected", False)
        check("Tab manager CDP connected", cdp_connected)
        check(f"Tabs synced", tab_count > 0, f"{tab_count} tabs")
    except Exception as e:
        check("Tab scan", False, str(e))

    # 5. Screenshot
    print("\n[5/9] Screenshot Capture")
    try:
        d = http_get(f"{BACKEND}/api/v1/tabs/status")
        cache = d.get("screenshot_cache_count", 0)
        tabs = d.get("tab_count", 0)
        check("Screenshot cache", cache > 0, f"{cache}/{tabs} cached")
        if cache == 0 and tabs > 0:
            tids = list(d.get("targets", {}).keys())
            if tids:
                try:
                    r = urllib.request.urlopen(f"{BACKEND}/api/v1/tabs/{tids[0]}/screenshot", timeout=8)
                    sd = json.loads(r.read())
                    has_img = bool(sd.get("screenshot_b64"))
                    check("On-demand screenshot", has_img, f"tab={tids[0][:20]}")
                except Exception as e:
                    check("On-demand screenshot", False, str(e)[:60])
    except Exception as e:
        check("Screenshot", False, str(e))

    # 6. Mistral API
    print("\n[6/9] Mistral API Key")
    try:
        d = http_get(f"{BACKEND}/api/v1/tabs/diagnostic")
        key_ok = d.get("checks", {}).get("mistral_api_key", {}).get("ok", False)
        engine = d.get("checks", {}).get("browser_engine", {}).get("engine", "?")
        check("Mistral API key set", key_ok)
        check("Browser engine", True, engine)
    except Exception as e:
        check("Mistral API check", False, str(e)[:60])

    # 7. WebSocket
    print("\n[7/9] WebSocket Connection")
    try:
        import websocket
        ws = websocket.create_connection("ws://localhost:8080/ws", timeout=3)
        ws.send("ping")
        check("Backend WebSocket", True)
        ws.close()
    except Exception as e:
        check("Backend WebSocket", False, str(e)[:60])

    # 8. Agent submission (dry run — only if CDP is working)
    print("\n[8/9] Agent Task Submission")
    if ws_ok:
        try:
            d = http_get(f"{BACKEND}/api/v1/tabs/status")
            tids = list(d.get("targets", {}).keys())
            if tids:
                body = {
                    "instructions": [{"tab_id": tids[0], "instruction": "Test: just report the page title"}],
                    "global_task": "",
                }
                r = http_post(f"{BACKEND}/api/v1/tabs/execute", body)
                check("Task submitted", r.get("status") == "executing", f"tabs={r.get('tab_count')}")
            else:
                check("Task submission", False, "No tabs to execute on")
        except Exception as e:
            check("Task submission", False, str(e)[:60])
    else:
        check("Task submission (skipped)", False, "CDP WebSocket not working — fix Chrome first")

    # 9. Full diagnostic
    print("\n[9/9] Full Diagnostic Endpoint")
    try:
        d = http_get(f"{BACKEND}/api/v1/tabs/diagnostic")
        all_ok = d.get("all_ok", False)
        check("Diagnostic all_ok", all_ok, json.dumps({k: v.get("ok", "n/a") for k, v in d.get("checks", {}).items() if isinstance(v, dict) and "ok" in v}))
    except Exception as e:
        check("Diagnostic endpoint", False, str(e)[:60])

    # Summary
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"\n{'='*40}")
    print(f"  Results: {passed}/{total} passed")
    if passed < total:
        print(f"\n  Fix order:")
        if not targets:
            print(f"  1. Launch Chrome: chrome --remote-debugging-port=9222 --remote-allow-origins=*")
        elif not ws_ok:
            print(f"  1. Restart Chrome WITH: --remote-allow-origins=*")
        print(f"  2. Restart backend: python run.py")
        print(f"  3. Re-run this test: python test_pipeline.py")
    else:
        print(f"\n  All checks passed! The pipeline is ready.")
    print()


if __name__ == "__main__":
    main()
