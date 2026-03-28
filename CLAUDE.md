# Mindd — Hive Mind Browser Dashboard

## Vision
Hexagonal hive canvas showing all Chrome tabs. Click a tab hexagon → switches Chrome to that tab. Alt+Z in any Chrome tab → floating chatbar for sending tasks. Agents run in parallel; kill any agent from the dashboard. Queen answers stuck workers via LLM.

## How to Run
1. Chrome: `"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222`
2. Backend: `cd backend && uvicorn main:app --reload --port 8080`
3. Frontend: `cd frontend && npm run dev`  (Vite proxy: /api → :8080, /ws → ws://:8080)

## Architecture
- **Chrome CDP** (port 9222): screenshot cache (1s loop), input dispatch, navigate, activate tab, chatbar injection
- **FastAPI backend** (port 8080): routers, mind/ orchestration, services/
- **React + Vite frontend** (port 5173): ReactFlow hex canvas, Zustand store, WebSocket
- **Gemini API**: Queen = `gemini-3.1-pro-preview` (thinking model, needs `max_output_tokens > 256`), Worker = `gemini-3-flash-preview`, Chat = `gemini-3-flash-preview`
- **Dual browser engine** (`BROWSER_ENGINE` in config/.env):
  - `"playwright"` (default on Windows): Accessibility-tree agent via `page.locator("body").aria_snapshot()` + `page.get_by_role()`. Text-only, ~1-3s/step, ~4x fewer tokens. No screenshots needed.
  - `"browser-use"`: Full vision-based agent via browser-use library. ~4-8s/step with screenshots + 2 LLM calls.
- **Streaming chat**: `POST /api/v1/chat/stream` SSE endpoint with live agent context injection
- **Queen narration**: `QUEEN_COMMENTARY` WebSocket events broadcast every 3 agent steps

## Key Files

### Backend
- `backend/main.py` — FastAPI app, lifespan (chrome sync loop + screenshot loop + chatbar auto-inject)
- `backend/services/tab_manager.py` — CDP integration, screenshot cache, `activate_tab()`, `inject_chatbar()`, `get_page_text()`, `_chatbar_injected` set
- `backend/services/browser_manager.py` — dual engine dispatch (playwright/browser-use), `_PlaywrightHandle`, `kill_agent()`, `_agent_tasks` dict
- `backend/mind/queen.py` — orchestrator, `answer_query()` for worker guidance, `_active_memory` global, `get_active_memory()`
- `backend/mind/worker.py` — worker: runs browser agent, HITL, broadcasts status, `_query_queen()` on error, `_broadcast_queen_commentary()` every 3 steps
- `backend/models/events.py` — WebSocket event constructors
- `backend/routers/tabs.py` — REST: scan, open, close, navigate, screenshot, input, activate, save-to-memory
- `backend/routers/tasks.py` — REST: submit task, queen-query endpoint
- `backend/routers/agents.py` — REST: list agents, get logs, DELETE kill agent

### Frontend
- `frontend/src/store/useMindStore.ts` — Zustand: tabs, agents, screenshots, selectedTabId, `killAgent()`
- `frontend/src/store/useWebSocket.ts` — WS connection, maps events → store
- `frontend/src/hooks/useAgentNodes.ts` — hex spiral layout with domain clustering, computes ReactFlow nodes/edges
- `frontend/src/components/MindMap/HiveGraph.tsx` — ReactFlow canvas (no InteractiveTabViewer)
- `frontend/src/components/MindMap/TabNode.tsx` — flat-top hexagon clip-path node, hover overlay (close + save-to-memory), single/double-click
- `frontend/src/components/MindMap/WorkerNode.tsx` — agent circle node with kill button on hover
- `frontend/src/components/Dashboard/CommandBar.tsx` — terminal input, task/chat modes, SSE streaming chat, tab routing
- `frontend/src/components/Dashboard/AgentLogPanel.tsx` — agent logs + kill button (Trash2 icon) per running agent
- `frontend/src/components/Tabs/TabPanel.tsx` — right drawer: tab list + instruction inputs
- `frontend/src/components/Tabs/TabGridPanel.tsx` — fullscreen tab grid overlay (G key), click → activate Chrome tab
- `frontend/src/App.tsx` — layout, keyboard shortcuts (T=tabs, L=logs, G=grid, Ctrl+K=focus)

## Tab Node (Hexagon)
- Shape: `clip-path: polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%)` (200×174px)
- **Single click** → select tab (highlight)
- **Double click** → `POST /api/v1/tabs/{tab_id}/activate` (Chrome switches to that tab)
- **Hover** → shows close (X) and save-to-memory (bookmark) buttons
- **Close button** → DELETE tab + kill assigned agent (if any)
- **Border effect** via `filter: drop-shadow()` (clip-path clips borders)

## Tab Activation
- `POST /api/v1/tabs/{tab_id}/activate` → `tab_manager.activate_tab()` → CDP `/json/activate/{target_id}`
- No InteractiveTabViewer — double-clicking a tab switches focus in the actual Chrome window

## Kill Agent
- `DELETE /api/v1/agents/{agent_id}` → cancels asyncio task, closes browser, broadcasts `AGENT_FAILED`
- Frontend: Trash2 button in AgentLogPanel (per running/planning agent) + kill button on WorkerNode hover
- Store: `killAgent(agentId)` removes agent from state immediately (optimistic)

## Alt+Z Chatbar Injection
- Backend auto-injects into every new Chrome tab via `tab_manager.inject_chatbar()`
- Persists across navigations via `Page.addScriptToEvaluateOnNewDocument`
- Shortcut: `Alt+Z` toggles the floating bar
- Submit → `POST /api/v1/tasks/submit` with `tab_id`
- "Save Page" button → `POST /api/v1/tabs/{tab_id}/save-to-memory`

## Queen Query (Worker ↔ Queen)
- Workers call `_query_queen()` in error handler
- `POST /api/v1/tasks/queen-query` → `answer_query()` using Gemini Pro + shared memory
- Response logged as "Queen guidance: ..." in agent log panel

## Queen Narration
- `_broadcast_queen_commentary()` fires on step 1 and every 3 steps (fire-and-forget)
- Calls `gemini_chat()` with a short narration prompt, broadcasts `QUEEN_COMMENTARY` via WebSocket
- Frontend shows as "Queen: ..." in the activity feed

## Streaming Chat
- `POST /api/v1/chat/stream` — SSE endpoint, returns `data: {"text": "..."}` chunks
- `_build_agent_context()` injects live agent status + completed results from memory
- Falls back to `POST /api/v1/chat/` (non-streaming) if stream fails
- System prompt switches to `CHAT_SYSTEM_AWARE` when agents are active

## Save to Memory
- `POST /api/v1/tabs/{tab_id}/save-to-memory` → scrapes page text via CDP, appends to `mind_memory.discovered_facts`
- Available from hex hover overlay (dashboard) and Alt+Z chatbar (injected into Chrome tabs)

## Hex Grid Layout
- Flat-top hexagons, axial coordinates: `HEX_SIZE=110`, 200×174px nodes
- Spiral outward from Queen at origin; tabs fill rings 1+ by domain clustering
- Domain clustering: tabs from same domain get contiguous spiral positions → visually adjacent

## Tab ID Convention
`cdp-{chromeTargetId}` — stable across rescans; filters out chrome://, devtools://, localhost dashboard

## Screenshot Architecture
- Background loop captures all tabs every 1s into `_screenshot_cache`
- GET `/screenshot` returns from cache instantly
- Frontend canvas polls at 5s for thumbnails

## WebSocket Events
TABS_UPDATE, AGENT_SPAWNED, AGENT_LOG, AGENT_STATUS, AGENT_COMPLETED, AGENT_FAILED, HITL_REQUEST, HITL_RESOLVED, VOICE_ANNOUNCEMENT, QUEEN_COMMENTARY

## Accessibility-Tree Engine Notes
- `page.locator("body").aria_snapshot()` returns YAML-format accessibility tree
- Actions use `page.get_by_role(role, name=name)` selectors (not CSS)
- `cancel_event: asyncio.Event` checked at top of each step for clean cancellation
- `generate_content_stream` must be `await`ed first, then `async for` iterated
- Gemini 3.1 Pro is thinking-only model — needs `max_output_tokens > 256` to produce output

## Keyboard Shortcuts
- `T` — toggle TabPanel drawer (right)
- `L` — toggle AgentLogPanel drawer (right)
- `G` — toggle TabGridPanel fullscreen overlay
- `Ctrl+K` — focus CommandBar
- `Escape` — close overlays / unfocus
- `Alt+Z` (in any Chrome tab) — toggle Mindd chatbar overlay
