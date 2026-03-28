# Team Task Board

## Quick Links
- [Full Implementation Plan](docs/PLAN.md)
- [Backend](backend/) | [Frontend](frontend/)

## Team Roles

| Person | Role | Focus Area |
|--------|------|------------|
| **Person A** | Dashboard Redesign + Demo + Pitch | Non-tech. Redesigns swarm dashboard in **Stitch** (Google), pitch deck, demo. No iMessage knowledge needed. |
| **Person B** | iMessage Kit + Bug Fixes | Photon iMessage Kit sidecar (TypeScript, macOS), existing backend bug fixes |
| **Person C** | Backend Logic | LangGraph redesign, MiniMax integration |
| **Person D** | Backend Logic | API routes, sender service, conversation store |

---

## Task Board

### Person A -- Dashboard Redesign + Demo + Pitch

Redesigns the existing swarm dashboard using **Stitch** (Google design tool). Only touches visuals -- the hex canvas, agent nodes, command bar, log panels. Knows nothing about iMessage, that's all backend.

- [ ] **A1** Redesign dashboard layout in Stitch -- hex canvas, page structure, spacing, color palette (4h) `P0`
- [ ] **A2** Redesign CommandBar, EventFeed ticker, AgentLogPanel for cleaner look (3h) `P0`
- [ ] **A3** Redesign QueenNode, WorkerNode, TabNode hex visuals (shapes, glows, status indicators) (3h) `P0`
- [ ] **A4** Add landing/hero page or onboarding screen for hackathon demo (2h) `P1`
- [ ] **A5** Build pitch deck -- "Text your AI" narrative, architecture diagrams, market positioning (4h) `P0`
- [ ] **A6** Prepare demo script + talking points (3-min flow) (2h) `P1`
- [ ] **A7** Record backup demo video (1h) `P2` -- needs working demo
- [ ] **A8** Apply Stitch designs to React components (with help from others if needed) (3h) `P1` -- after A1-A3

### Person B -- iMessage Kit + Bug Fixes

Owns the Photon iMessage Kit sidecar (TypeScript/Node.js, runs on macOS). Also fixes existing backend bugs. No frontend work -- iMessage is purely backend (phone <-> server <-> phone).

- [ ] **B1** Set up `backend/imessage-bridge/` Node.js project + install Photon SDK (1h) `P0`
- [ ] **B2** Implement Photon polling + webhook POST to FastAPI on new message (3h) `P0` -- after B1
- [ ] **B3** Implement `/send` endpoint for outbound iMessages (text + files) (2h) `P0` -- after B1
- [ ] **B4** Fix `worker.py` agent_logs memory leak (~L282) (0.5h) `P1`
- [ ] **B5** Fix `tab_manager.py` screenshot cache bloat (0.5h) `P1`
- [ ] **B6** Fix `queen.py` subtask dependency DAG execution (~L276-312) (2h) `P1`
- [ ] **B7** End-to-end test: iMessage -> swarm runs -> reply arrives on phone (2h) `P1` -- after B2, B3, C6

### Person C -- LangGraph + MiniMax (Backend Logic)

- [ ] **C1** Create `backend/services/minimax_client.py` using OpenAI SDK + MiniMax base_url (2h) `P0`
- [ ] **C2** Test intent classification with 10+ sample messages (1h) `P0` -- after C1
- [ ] **C3** Extend `backend/mind/state.py` with `HiveMindState` (1h) `P0`
- [ ] **C4** Rewrite `backend/mind/graph.py` with LangGraph intent routing flow (4h) `P0` -- after C1, C3
- [ ] **C5** Implement parallel chat graph `build_chat_graph()` (2h) `P1` -- after C4
- [ ] **C6** Wire graph invocation from `routers/imessage.py` webhook (1h) `P1` -- after C4, D1

### Person D -- API Routes + Sender Services (Backend Logic)

- [ ] **D1** Create `backend/routers/imessage.py` (webhook + send + conversations endpoints) (2h) `P0`
- [ ] **D2** Create `backend/services/imessage_sender.py` (HTTP client to bridge /send) (2h) `P0`
- [ ] **D3** Create `backend/services/conversation_store.py` + update config/events/main.py (2h) `P0`
- [ ] **D4** Implement iMessage status updates during swarm execution (2h) `P1` -- after D2, C4
- [ ] **D5** Screenshot-as-iMessage-attachment feature (1h) `P1` -- after D2
- [ ] **D6** Add MiniMax fallback-to-Gemini wrapper (1h) `P1` -- after C1

---

## Critical Path

```
C1 (minimax) --> C4 (graph) --> C6 (wire) --+
                                             |
D1 (router) + D2 (sender) + D3 (config) ---+--> B7 (e2e iMessage test)
                                             |
B1 (bridge) --> B2 (webhook) --> B3 (/send)-+

A1 (Stitch redesign) --> A8 (apply to React) --> A5 (pitch) --> DEMO
```

**Day 1 parallel starts**: C1 + D1 + D2 + D3 + B1 + A1 -- everyone independent, zero blockers.

Person A works entirely in Stitch -- no overlap with backend or iMessage work.

---

## Environment Setup

Each team member needs:

```bash
# Clone
git clone https://github.com/Kvndoshi/uschacks.git
cd uschacks

# Backend (Persons B, C, D)
cd backend
pip install -r requirements.txt
playwright install chromium
cp .env.template .env   # Fill in API keys

# Frontend (Person A for applying designs)
cd ../frontend
npm install

# iMessage Bridge (Person B only, macOS required)
cd ../backend/imessage-bridge
npm install
```

### Required API Keys (in `backend/.env`)

```
GEMINI_API_KEY=...          # Google AI Studio
MINIMAX_API_KEY=...         # platform.minimax.io
SUPERMEMORY_API_KEY=...     # Optional
ELEVENLABS_API_KEY=...      # Optional
IMESSAGE_BRIDGE_URL=http://localhost:3001
IMESSAGE_ENABLED=true
```

### Running

```bash
# Terminal 1: Chrome with CDP
chrome --remote-debugging-port=9222 --remote-allow-origins=*

# Terminal 2: Backend
cd backend && python run.py

# Terminal 3: Frontend
cd frontend && npm run dev

# Terminal 4: iMessage Bridge (macOS only)
cd backend/imessage-bridge && npm start
```

---

## Model Usage

| Role | Model | Cost |
|------|-------|------|
| Intent Classifier | MiniMax-M2.7 | $0.30/M input |
| Quick Answer | MiniMax-M2.7 | $0.30/M input |
| Chat Agent | MiniMax-M2.7 | $0.30/M input |
| Result Synthesizer | MiniMax-M2.7 | $0.30/M input |
| Queen Decomposer | Gemini 3.1 Pro | Existing |
| Worker Agents | Gemini 3 Flash | Existing |
