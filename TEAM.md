# Team Task Board

## Quick Links
- [Full Implementation Plan](docs/PLAN.md)
- [Backend](backend/) | [Frontend](frontend/)

## Team Roles

| Person | Role | Focus Area |
|--------|------|------------|
| **Person A** | UI/Demo/Pitch | Non-tech. Mockups, pitch deck, demo script |
| **Person B** | iMessage Bridge + Frontend | Photon iMessage Kit (TypeScript), iMessage UI panel |
| **Person C** | Backend Logic | LangGraph redesign, MiniMax integration |
| **Person D** | Backend Logic | API routes, sender service, bug fixes |

---

## Task Board

### Person A (UI + Demo + Pitch)

- [ ] **A1** Design iMessage panel mockup/wireframe (2h) `P0`
- [ ] **A2** Build pitch deck - "Text your AI" narrative + architecture diagrams (4h) `P0`
- [ ] **A3** Prepare demo script + talking points (2h) `P1`
- [ ] **A4** Record backup demo video (1h) `P2`

### Person B (iMessage Bridge + Frontend)

- [ ] **B1** Set up `backend/imessage-bridge/` Node.js project + install Photon SDK (1h) `P0`
- [ ] **B2** Implement Photon polling + webhook POST to FastAPI (3h) `P0`
- [ ] **B3** Implement `/send` endpoint for outbound iMessages (2h) `P0` -- blocked by B1
- [ ] **B4** Build `iMessagePanel.tsx` + `ConversationBubble.tsx` (3h) `P1` -- blocked by A1
- [ ] **B5** Wire WebSocket iMessage events in frontend store (1h) `P1` -- blocked by D3
- [ ] **B6** Add iMessage panel toggle to `App.tsx` (1h) `P1` -- blocked by B4
- [ ] **B7** End-to-end test: iMessage -> dashboard -> reply (2h) `P1` -- blocked by all above

### Person C (LangGraph + MiniMax)

- [ ] **C1** Create `backend/services/minimax_client.py` using OpenAI SDK (2h) `P0`
- [ ] **C2** Test intent classification with 10+ sample messages (1h) `P0` -- blocked by C1
- [ ] **C3** Extend `backend/mind/state.py` with `HiveMindState` (1h) `P0`
- [ ] **C4** Rewrite `backend/mind/graph.py` with LangGraph intent routing (4h) `P0` -- blocked by C1, C3
- [ ] **C5** Implement parallel chat graph `build_chat_graph()` (2h) `P1` -- blocked by C4
- [ ] **C6** Wire graph invocation from `routers/imessage.py` (1h) `P1` -- blocked by C4, D1

### Person D (Router/Sender + Bug Fixes)

- [ ] **D1** Create `backend/routers/imessage.py` (webhook + send + conversations) (2h) `P0`
- [ ] **D2** Create `backend/services/imessage_sender.py` (bridge HTTP client) (2h) `P0`
- [ ] **D3** Create `backend/services/conversation_store.py` + update config/events/main (2h) `P0`
- [ ] **D4** Fix `worker.py` agent_logs memory leak (~L282) (0.5h) `P1`
- [ ] **D5** Fix `tab_manager.py` screenshot cache bloat (0.5h) `P1`
- [ ] **D6** Fix `queen.py` subtask dependency DAG execution (~L276-312) (2h) `P1`
- [ ] **D7** Implement iMessage status updates during swarm execution (2h) `P1` -- blocked by D2, C4
- [ ] **D8** Screenshot-as-iMessage-attachment feature (1h) `P2` -- blocked by D2

---

## Critical Path

```
C1 (minimax client) --> C4 (graph rewrite) --+
                                              |
D1 (router) + D2 (sender) + D3 (config) ----+--> C6 (wire together) --> B7 (e2e test)
                                              |
B1 (bridge) --> B2 (webhook) --> B3 (/send) -+
                                              |
A1 (mockup) --> B4 (panel) --> B6 -----------+--> DEMO
```

**Start here**: C1 + D1 + D2 + D3 + B1 can all begin in parallel on Day 1.

---

## Environment Setup

Each team member needs:

```bash
# Clone
git clone https://github.com/Kvndoshi/uschacks.git
cd uschacks

# Backend
cd backend
pip install -r requirements.txt
playwright install chromium
cp .env.template .env   # Fill in API keys

# Frontend
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
