<p align="center">
  <img src="https://img.shields.io/badge/HIVEMIND-Swarm_Intelligence-blueviolet?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiPjxwYXRoIGQ9Ik0xMiAyTDIgN2wxMCA1IDEwLTV6Ii8+PHBhdGggZD0iTTIgMTdsMTAgNSAxMC01Ii8+PHBhdGggZD0iTTIgMTJsMTAgNSAxMC01Ii8+PC9zdmc+" alt="Hivemind Badge"/>
</p>

<h1 align="center">HIVEMIND v2</h1>
<h3 align="center">Text Your AI. Command a Swarm.</h3>

<p align="center">
  iMessage-controlled AI browser swarm for productivity and life hacks.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/react-19-61DAFB?logo=react&logoColor=white" alt="React"/>
  <img src="https://img.shields.io/badge/MiniMax-M2.7-FF6B35?style=flat&logoColor=white" alt="MiniMax"/>
  <img src="https://img.shields.io/badge/gemini-3_pro-4285F4?logo=google&logoColor=white" alt="Gemini"/>
  <img src="https://img.shields.io/badge/iMessage-Photon_Kit-34C759?logo=apple&logoColor=white" alt="iMessage"/>
  <img src="https://img.shields.io/badge/LangGraph-orchestrated-purple" alt="LangGraph"/>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License"/>
</p>

---

## What is HIVEMIND v2?

HIVEMIND v2 turns any iPhone into a command center for an AI browser swarm. Send an iMessage, and HIVEMIND classifies your intent, deploys coordinated browser agents, and texts you back the results. No app install needed.

```
You (iMessage):  "Compare AirPods Pro prices on Amazon vs Best Buy"
HIVEMIND:        "Deploying 2 agents..."
                  --> Agent 1: navigating Amazon.com
                  --> Agent 2: navigating BestBuy.com
HIVEMIND:        "Amazon: $189.99 (Prime) | Best Buy: $179.99 (open box)
                  Best deal: Best Buy open-box saves $10"

You (iMessage):  "What's the battery life?" (while swarm is running)
HIVEMIND:        "AirPods Pro 2 offers up to 6h listening, 30h with case"
                  (answered instantly by chat agent while swarm works)
```

### Architecture

```
iPhone (iMessage) --> Photon iMessage Kit (macOS)
    --> FastAPI + LangGraph Router
        --> MiniMax-M2.7: intent classification + chat + synthesis
        --> Gemini 3 Pro: Queen task decomposition
        --> Gemini 3 Flash: Worker browser agents (CDP)
    --> Results sent back via iMessage
```

---

## Original: What is Hivemind?

Hivemind is an AI-powered browser orchestration system that transforms your web browser into a fully autonomous command center. Give it a task in natural language — or just speak — and it deploys coordinated swarms of intelligent agents that take over your browser tabs, work in parallel across multiple websites, and deliver consolidated results in seconds.

```
You:    "Find me the cheapest nonstop flight from PHX to SFO tomorrow across all major platforms"
Queen:  → Agent 1 dispatched to Google Flights
        → Agent 2 dispatched to Expedia
        → Agent 3 dispatched to Kayak
Result: Consolidated comparison in 30 seconds
```

## Demo Video

- YouTube demo: [https://youtu.be/CViX61F9_W4](https://youtu.be/CViX61F9_W4)
- Click to watch:

[![Watch HIVEMIND demo](https://img.youtube.com/vi/CViX61F9_W4/maxresdefault.jpg)](https://youtu.be/CViX61F9_W4)

---

## Features

### Swarm Orchestration Engine
A central AI orchestrator (the **Queen**) powered by Gemini decomposes any high-level request into optimized subtasks, assigns dedicated agents, allocates browser tabs intelligently, and synthesizes results — all without human intervention.

### Parallel Multi-Agent Execution
Agents run fully async and concurrently. Search flights on Google Flights, Expedia, and Kayak at the same time. Compare products across Amazon, Best Buy, and Walmart in a single prompt. No waiting, no tab switching.

### Live Browser Control via CDP
Agents control your **real Chrome browser** through Chrome DevTools Protocol. They click, type, scroll, navigate, and read pages exactly like a human would — in your actual browser tabs where you can watch it live.

### Neural Link — Real-Time Agent Feed
A live telemetry stream of every agent action, decision, and result. See what each agent is doing, which page it's on, what it clicked, and when it's done — full transparency into the swarm.

### Visual Tab Clustering & Management
All open tabs displayed as live visual previews, automatically grouped by topic using AI-powered clustering. Open, close, capture, or navigate to any tab directly from the dashboard.

### Page Capture & Instant Memory
Capture any webpage with one click and store it into persistent memory. Captured pages become searchable context for future tasks — building an ever-growing knowledge base.

### Supermemory — Human-Like Memory System
Connected to [Supermemory](https://supermemory.com) for both short-term and long-term memory. Short-term tracks session context. Long-term stores preferences, past results, and behavioral patterns. The system remembers your preferred airlines, favorite retailers, email style — and applies it automatically.

### Adaptive Preference Learning
Every interaction trains Hivemind. It learns your preferred websites, communication style, search patterns, and decision criteria. Over time it stops asking and starts knowing.

### Voice-Commanded Browser Control
Speak naturally and Hivemind listens. Voice-to-action pipeline converts speech into orchestrated browser operations in real time. Powered by ElevenLabs STT.

```
🎤 "Draft an email to Sarah about tomorrow's meeting"
→ Agent opens Gmail → Composes draft → Waits for approval
```

### Human-in-the-Loop Safety
Before any sensitive action — sending an email, submitting a form, making a purchase — agents pause and ask for explicit approval. You stay in control of every irreversible action.

### Queen Narration — Live Commentary
The Queen AI periodically narrates what each agent is doing in plain language, broadcast as real-time WebSocket events. You always know what's happening without reading raw logs.

### Streaming Context-Aware Chat
Ask "what's happening?" while agents run and get a streaming SSE response with live agent status injected into context. The AI knows which agents are running, what step they're on, and what they've found so far.

### Smart Context-Aware Decomposition
The orchestrator understands intent. "Plan my trip to San Francisco" triggers flight search, hotel comparison, restaurant recommendations, and calendar blocking as coordinated subtasks with shared context. Each agent gets explicit boundaries — "Only work on [site]. Do NOT navigate elsewhere."

### Cross-Site Data Fusion
Agents synthesize across sources. Compare prices from five retailers, merge reviews from Reddit and YouTube, consolidate news from multiple outlets — all fused into a single structured answer.

### Chat With Your Memory
A conversational interface to your entire browsing history. Ask questions, retrieve past results, explore preferences, or get recommendations — powered by semantic search.

### Automated Workflow Chains
```
"Every morning: summarize unread emails, check calendar, pull top tech news, draft daily briefing"
```
Multi-step workflows executed as coordinated agent pipelines.

### Form Auto-Fill & Repetitive Task Automation
Job applications, expense reports, registrations — Hivemind fills them using your stored profile. Repetitive tasks that took minutes now take seconds.

### Protected Dashboard Mode
Agents are prohibited from navigating to or modifying the Hivemind dashboard. Your command center is always safe.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     HIVEMIND DASHBOARD                       │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐  ┌────────────┐  │
│  │ Command  │  │  Neural  │  │   Tab     │  │   Chat /   │  │
│  │   Bar    │  │   Link   │  │  Cluster  │  │  Memory    │  │
│  │  + Voice │  │   Feed   │  │  Preview  │  │  Panel     │  │
│  └────┬─────┘  └────▲─────┘  └─────▲─────┘  └─────▲──────┘  │
│       │              │              │              │          │
│       │         WebSocket      CDP Screenshots     │          │
│       ▼              │              │              │          │
│  ┌───────────────────┴──────────────┴──────────────┘          │
│  │              React + Zustand + Framer Motion              │
│  └───────────────────────────┬───────────────────────────────┘│
└──────────────────────────────┼────────────────────────────────┘
                               │ HTTP + WebSocket
┌──────────────────────────────┼────────────────────────────────┐
│                      FASTAPI BACKEND                          │
│  ┌───────────────────────────▼───────────────────────────┐    │
│  │                 QUEEN (Gemini 3 Pro)                   │    │
│  │        Task Decomposition · Tab Allocation            │    │
│  │        Context Synthesis · Result Aggregation          │    │
│  └──┬──────────┬──────────┬──────────┬───────────────────┘    │
│     │          │          │          │                         │
│  ┌──▼──┐   ┌──▼──┐   ┌──▼──┐   ┌──▼──┐                     │
│  │Agent│   │Agent│   │Agent│   │Agent│  (Gemini 3 Flash)     │
│  │  1  │   │  2  │   │  3  │   │  N  │                       │
│  └──┬──┘   └──┬──┘   └──┬──┘   └──┬──┘                      │
│     │         │         │         │                           │
│     └─────────┴────┬────┴─────────┘                          │
│                    │                                          │
│              ┌─────▼─────┐     ┌──────────────┐              │
│              │ browser-  │     │ Supermemory   │              │
│              │   use     │     │  (Long-term)  │              │
│              │  via CDP  │     │  (Short-term) │              │
│              └─────┬─────┘     └──────────────┘              │
└────────────────────┼──────────────────────────────────────────┘
                     │ Chrome DevTools Protocol
              ┌──────▼──────┐
              │   Chrome    │
              │  (Real      │
              │   Browser)  │
              └─────────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google Chrome with remote debugging enabled

### 1. Clone

```bash
git clone https://github.com/Kvndoshi/hivemind.git
cd hivemind
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
```

Create `.env` from the template:

```bash
cp .env.template .env
```

Fill in your API keys:

```env
GEMINI_API_KEY=your_gemini_key               # required — powers all LLM calls
ELEVENLABS_API_KEY=your_elevenlabs_key       # optional, for voice
SUPERMEMORY_API_KEY=your_supermemory_key     # optional, for memory
```

Start the backend:

```bash
python run.py
```

Windows CMD (recommended):

```cmd
cd /d C:\Users\kevin\vscode_files\mistralhackathon\backend
set PORT=8081
py run.py
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** (or `5174` if Vite auto-switches ports) — Hivemind is ready.

Start remote Chrome for CDP:

```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir=C:\Users\kevin\chrome-debug-profile
```

---

## Usage

### Text Commands

Type any task into the command bar:

| Prompt | What Happens |
|--------|-------------|
| `Find cheapest flights from PHX to SFO tomorrow` | Spawns agents on Google Flights, Expedia |
| `Compare 34 inch monitors on Amazon` | Agent searches, extracts specs, returns comparison |
| `Summarize my unread Gmail and draft replies` | Agent opens Gmail, reads, drafts with approval |
| `Fill out this job application with my info` | Auto-fills using stored profile from memory |

### Voice Commands

Click the microphone icon and speak naturally. Your voice is transcribed and executed as a command.

### Chat With Memory

Use the chat panel to query your accumulated context:
- *"What flights did I search last week?"*
- *"What are my monitor preferences?"*
- *"Show me my saved pages about React"*

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Orchestrator LLM** | Gemini 3.1 Pro (Queen) with 2.5 Flash fallback |
| **Agent LLM** | Gemini 3 Flash (Workers + Chat) |
| **Browser Automation** | browser-use + Chrome DevTools Protocol |
| **Backend** | FastAPI, Python, asyncio, WebSockets |
| **Frontend** | React 18, TypeScript, Zustand, Framer Motion, Tailwind CSS |
| **Tab Visualization** | React Flow (xyflow) |
| **Memory** | Supermemory SDK (long-term + short-term) |
| **Voice** | ElevenLabs TTS + Web Audio STT |
| **Real-time Comms** | WebSocket events + SSE streaming chat |
| **Deployment** | Google Cloud Run, Cloud Build, Docker |

---

## Project Structure

```
hivemind/
├── backend/
│   ├── main.py                  # FastAPI app + lifespan
│   ├── run.py                   # Entry point (uvicorn)
│   ├── config.py                # All configuration
│   ├── mind/
│   │   ├── queen.py             # Orchestrator — task decomposition
│   │   ├── worker.py            # Agent execution loop
│   │   ├── memory.py            # Shared ephemeral memory
│   │   └── sensitive.py         # HITL action detection
│   ├── services/
│   │   ├── mistral_client.py    # LLM gateway (Gemini-powered orchestration/chat)
│   │   ├── browser_manager.py   # browser-use agent lifecycle
│   │   ├── tab_manager.py       # CDP tab scanning + assignment
│   │   ├── supermemory_service.py  # Persistent memory layer
│   │   ├── elevenlabs_service.py   # TTS + STT
│   │   └── websocket_manager.py    # WS broadcast
│   ├── routers/
│   │   ├── tasks.py             # POST /api/v1/tasks/submit
│   │   ├── tabs.py              # Tab CRUD + screenshots
│   │   ├── chat.py              # Memory chat
│   │   ├── voice.py             # Voice transcription
│   │   ├── memory.py            # Memory save/search
│   │   └── agents.py            # Agent control
│   ├── models/
│   │   └── events.py            # WebSocket event types
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Main layout
│   │   ├── store/
│   │   │   ├── useMindStore.ts  # Zustand state
│   │   │   └── useWebSocket.ts  # WS event handler
│   │   ├── components/
│   │   │   ├── Dashboard/
│   │   │   │   ├── CommandBar.tsx    # Input + voice
│   │   │   │   └── AgentLogPanel.tsx # Results display
│   │   │   ├── MindMap/
│   │   │   │   ├── HiveGraph.tsx     # React Flow graph
│   │   │   │   ├── TabNode.tsx       # Tab preview node
│   │   │   │   └── WorkerNode.tsx    # Agent node
│   │   │   └── Tabs/
│   │   │       ├── TabPanel.tsx      # Tab list
│   │   │       └── TabGridPanel.tsx  # Grid view
│   │   └── types/
│   │       └── mind.types.ts
│   └── vite.config.ts
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/tasks/submit` | Submit a task for orchestration |
| `GET` | `/api/v1/tabs/scan` | Scan Chrome tabs via CDP |
| `GET` | `/api/v1/tabs/:id/screenshot` | Get tab screenshot |
| `POST` | `/api/v1/chat/` | Chat with memory (non-streaming) |
| `POST` | `/api/v1/chat/stream` | SSE streaming chat with live agent context |
| `POST` | `/api/v1/voice/transcribe` | Transcribe voice to text |
| `POST` | `/api/v1/memory/save` | Save to Supermemory |
| `POST` | `/api/v1/memory/search` | Search memory |
| `WS` | `/ws` | Real-time event stream |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key (powers Queen, Workers, and Chat) |
| `ELEVENLABS_API_KEY` | No | ElevenLabs key for voice features |
| `SUPERMEMORY_API_KEY` | No | Supermemory key for persistent memory |
| `BROWSER_ENGINE` | No | `browser-use` (default) or `playwright` |
| `AGENT_MAX_STEPS` | No | Max steps per agent (default: 30) |
| `AGENT_TIMEOUT_SECONDS` | No | Agent timeout (default: 600) |

---

## How It Works

1. **You speak or type** a task
2. **Queen (Gemini)** analyzes intent, checks memory for preferences, scans open tabs
3. **Decomposition** — task split into parallel subtasks with tab assignments
4. **Agents (Gemini Flash)** spawn concurrently, each controlling a real Chrome tab via CDP
5. **Execution** — agents navigate, click, extract data, with HITL pauses for sensitive actions
6. **Synthesis** — Queen aggregates all agent results into a final answer
7. **Memory** — task input, output, and discovered preferences saved to Supermemory

---

## Google Cloud Deployment

The backend is deployed to **Google Cloud Run** via Cloud Build:

```bash
# Set your Gemini API key and deploy
export GEMINI_API_KEY=your_key_here
bash deploy.sh
```

**Proof of Google Cloud usage:**
- [`cloudbuild.yaml`](cloudbuild.yaml) — Cloud Build pipeline: Docker build → GCR push → Cloud Run deploy
- [`Dockerfile`](Dockerfile) — Python 3.11 container with Playwright + backend
- [`deploy.sh`](deploy.sh) — Deployment script using `gcloud builds submit`
- All LLM calls route through **Google Gemini API** (`google-genai` SDK) — see [`backend/services/mistral_client.py`](backend/services/mistral_client.py) (LLM gateway module) and [`backend/config.py`](backend/config.py)

---

## Submission Assets (Hackathon)

### 1) Text Description
This README includes:
- feature and functionality summary
- technologies used
- data/context sources (web pages via browser/CDP + Supermemory context)
- findings and learnings

### 2) Public Code Repository
- GitHub: [https://github.com/Kvndoshi/hivemind](https://github.com/Kvndoshi/hivemind)

### 3) Spin-up / Reproducibility
- Full local spin-up instructions are in the **Quick Start** section above.

### 4) Proof of Google Cloud Deployment
Use either of the following:
- screen recording of Cloud Run service + logs, or
- code links proving Google Cloud usage:
  - [`cloudbuild.yaml`](cloudbuild.yaml)
  - [`Dockerfile`](Dockerfile)
  - [`deploy.sh`](deploy.sh)
  - [`backend/services/mistral_client.py`](backend/services/mistral_client.py) (Gemini LLM gateway)

### 5) Architecture Diagram
- Included in this README under **Architecture** (ASCII diagram).
- Optional: export this diagram as image (`docs/architecture.png`) and attach it in submission carousel for judges.

### 6) Demonstration Video (<4 minutes)
- Demo link: [https://youtu.be/CViX61F9_W4](https://youtu.be/CViX61F9_W4)
- Should show real-time multimodal + agentic workflows (no mockups), problem statement, and value delivered.

### 7) Optional Bonus Points

#### 7.1 Published Content (Max 0.6)
- Content URL: [https://youtu.be/CViX61F9_W4](https://youtu.be/CViX61F9_W4)
- Required disclosure language:
  - "I created this piece of content for the purposes of entering the Gemini Live Agent Challenge hackathon."
- Social hashtag:
  - `#GeminiLiveAgentChallenge`

#### 7.2 Automated Cloud Deployment (Max 0.2)
- Deployment automation code links:
  - [`cloudbuild.yaml`](cloudbuild.yaml)
  - [`deploy.sh`](deploy.sh)
  - [`Dockerfile`](Dockerfile)

#### 7.3 Public Google Developer Group (GDG) Profile (Max 0.2)
- Add your public GDG profile URL before final submission:
  - `https://<your-public-gdg-profile-url>`

## Findings & Learnings

1. **Per-agent Browser instances are critical** — Sharing a single browser-use `Browser` object across agents causes cascading 30s timeouts due to event bus contention. Each agent needs its own CDP connection.

2. **Gemini model selection matters** — Gemini 3.1 Pro is a thinking model that needs `max_output_tokens > 256` to produce output. Gemini 3 Flash is faster for workers. Wrong model = wasted time and tokens.

3. **Multi-agent coordination needs explicit boundaries** — Without "only work on [site]" instructions, agents wander to the same websites. The Queen must produce self-contained, non-overlapping tasks.

4. **HITL prevents costly mistakes** — Agents confidently click "Send" on emails. Human-in-the-loop with timeouts catches these before real-world consequences.

5. **Streaming chat with agent context creates presence** — When users ask "what's happening?" and get live agent status in the response, the system feels alive rather than opaque.

6. **WebSocket event architecture scales** — Broadcasting granular events (spawned, log, status, completed, failed, HITL, Queen commentary) lets the frontend render exactly what it needs.

---

## License

MIT

---

<p align="center">
  <b>One voice. One command. A swarm of agents. Your browser, supercharged.</b>
</p>
