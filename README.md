# AI-First CRM — HCP Log Interaction Module

![React](https://img.shields.io/badge/Frontend-React%20%2B%20Redux-61DAFB?style=flat-square&logo=react&logoColor=white)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/AI%20Agent-LangGraph-1C3C3C?style=flat-square)
![Groq](https://img.shields.io/badge/LLM-Groq%20(llama--3.1--8b--instant)-F55036?style=flat-square)
![Postgres](https://img.shields.io/badge/Database-PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Status](https://img.shields.io/badge/Status-Working-brightgreen?style=flat-square)

An AI-first CRM module for pharmaceutical field representatives to log interactions with Healthcare Professionals (HCPs) — either through a **structured form** or a **conversational chat interface**, powered by a LangGraph agent.

The form and the chat panel are two views of the **same underlying state**. A rep describes a visit in plain English, and the AI agent extracts structured fields — HCP name, sentiment, topics, materials shared, and more — and fills the form live. The rep can also correct or extend the log conversationally, and save the finished record to the database.

---

## 📋 Task Requirements Checklist

| Requirement | Status |
|---|:---:|
| Log Interaction Screen (form + chat) | ✅ |
| React frontend with Redux | ✅ |
| Python backend with FastAPI | ✅ |
| LangGraph AI agent framework | ✅ |
| Groq LLM integration | ✅ (see model note below) |
| PostgreSQL database | ✅ |
| Google Inter font | ✅ |
| Minimum 5 LangGraph tools | ✅ (5 tools — see below) |
| `log_interaction` tool | ✅ |
| `edit_interaction` tool | ✅ |

---

## 💡 Why an AI-First Design?

Field reps spend a large share of their day on manual CRM data entry after a visit, which leads to sparse, delayed, or inconsistent logs. This module treats the LLM agent as the **primary data-entry interface**: the rep just talks about the visit the way they naturally would, and the agent turns that into structured CRM data — while still leaving the structured form fully visible as a live view of that same data.

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Redux (state management), Vite |
| Backend | Python, FastAPI |
| AI Agent Framework | LangGraph |
| LLM | Groq API — `llama-3.3-70b-versatile` (see note below) |
| Database | PostgreSQL (hosted on Supabase) |
| Font | Google Inter |

> **⚠️ Note on the LLM model:** The task specification calls for Groq's `gemma2-9b-it`. As of this submission, Groq has **officially deprecated `gemma2-9b-it`**, recommending `llama-3.3-70b-versatile` as the direct replacement, describing it as delivering comparable price-performance at the same speed. This project uses `llama-3.3-70b-versatile` accordingly. The model is fully configurable via the `GROQ_MODEL` environment variable, so it can be swapped back if `gemma2-9b-it` becomes available again.

---

## 📁 Project Structure

```
HCP_CRM/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app, routes: /health, /chat, /interactions
│   │   ├── agent.py         # LangGraph agent graph definition + system prompt
│   │   ├── tools.py         # 5 LangGraph tools used by the agent
│   │   ├── models.py        # SQLAlchemy ORM model (Interaction table)
│   │   ├── schemas.py       # Pydantic request/response schemas
│   │   ├── database.py      # DB engine/session setup
│   │   └── config.py        # Env-based configuration
│   ├── tests/                # Basic backend tests
│   ├── requirements.txt
│   └── .env                 # Not committed — see Setup below
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── InteractionForm.jsx   # Structured form (left panel)
    │   │   └── AIChatPanel.jsx       # Conversational AI panel (right panel)
    │   ├── redux/
    │   │   ├── interactionSlice.js   # Form state
    │   │   └── chatSlice.js          # Chat messages/loading state
    │   ├── api/
    │   │   └── client.js             # Calls to /chat and /interactions
    │   ├── App.jsx
    │   └── main.jsx
    └── package.json
```

---

## 🤖 The LangGraph Agent

### Role

Per the task's requirement to describe the agent's role in managing HCP interactions: the agent sits behind the `/chat` endpoint and acts as the intermediary between the rep's free-text description of a visit and the structured `Interaction` record. On every message, it decides — using the LLM as a router — which tool(s) to call based on the conversation so far and the current form state, executes them, merges their results into the form, and replies to the rep in plain language confirming what changed.

The graph runs as a loop: **agent → (tools → apply_updates) → agent → END**, so the model can chain multiple relevant tool calls in one turn — for example logging the visit *and* suggesting materials *and* scheduling a follow-up from a single message — before handing control back to the rep. The loop is bounded by both a per-turn tool-call cap and a rule against calling the same tool twice in one turn, so the agent always terminates cleanly.

### The 5 Tools

| Tool | Function |
|---|---|
| 📝 `log_interaction` | Extracts structured interaction details from natural language |
| ✏️ `edit_interaction` | Modifies a single field on an existing interaction |
| 📄 `suggest_materials` | Recommends relevant HCP materials based on topics discussed |
| 📅 `schedule_followup` | Schedules follow-up actions with a computed due date |
| 📊 `summarize_hcp_history` | Retrieves and summarizes past HCP interactions |

**1. `log_interaction`** — Called the first time a visit is described. The LLM performs entity extraction directly through structured tool-calling: it reads the rep's natural-language description and extracts HCP name, interaction type, date, time, attendees, topics discussed, sentiment, outcomes, and follow-up actions as individual arguments, which are then merged into the form state.

**2. `edit_interaction`** — Called when the rep corrects or updates a single field on an already-logged interaction (e.g. *"actually the sentiment was negative"*). Takes a `field` + `value` pair and updates only that field, leaving the rest of the form untouched.

**3. `suggest_materials`** — Given the topics discussed, matches against a materials catalog (efficacy, safety, dosage, trial data, etc.) and adds relevant suggested materials to `materials_shared`.

**4. `schedule_followup`** — Given an action and a number of days out (default 14), computes a due date and appends a follow-up entry to `follow_up_actions` without overwriting any existing follow-ups.

**5. `summarize_hcp_history`** — Queries the database for prior logged interactions with the named HCP and summarizes sentiment trend and past outcomes, giving the rep context before logging today's visit.

---

## ⚙️ Setup & Run

### Prerequisites
- Python 3.11+
- Node.js 18+
- A Groq API key ([console.groq.com](https://console.groq.com))
- A PostgreSQL database (this project uses Supabase's session pooler, but any Postgres instance works)

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

Create a `.env` file inside `backend/`:

```dotenv
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
DATABASE_URL=postgresql+psycopg://user:password@host:5432/dbname
CORS_ORIGINS=http://localhost:5173
```

Run the server:

```bash
uvicorn app.main:app --reload
```

- API docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

- App: `http://localhost:5173`

---

## 🔌 API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/chat` | Send a rep message + current form state + chat history; returns AI reply, updated form state, and list of tools invoked |
| POST | `/interactions` | Persist the current form state as a saved Interaction record |
| GET | `/interactions` | List all saved interactions |

---

## 📌 Known Limitations / Notes

- `date`/`time` are stored as plain strings rather than native `Date`/`Time` types, since the LLM naturally outputs them as text (`DD-MM-YYYY`, `HH:MM`).
- The form fields are read-only by design — all data entry happens through the AI chat panel, with a "Save Interaction" action to persist the current state.
- `gemma2-9b-it` was substituted with `llama-3.3-70b-versatile` per Groq's own deprecation guidance (see note above).

---

## 🎥 Submission

- **GitHub Repository:** this repo
- **Video Walkthrough:** 10–15 min recording covering frontend walkthrough, all 5 tools demoed live, code structure explanation, and a summary of the task

---

## 👤 Author

Built by Kishore Raja as part of a technical assignment for an AI-First CRM HCP Module (Log Interaction Screen) task.