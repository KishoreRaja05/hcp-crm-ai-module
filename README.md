# AI-First CRM — HCP Log Interaction Module

An AI-first CRM module for pharmaceutical field representatives to log interactions with Healthcare Professionals (HCPs) — either through a structured form or a natural-language chat interface powered by a LangGraph agent.

The chat interface and the form are two views of the **same underlying state**: describe a visit in plain English, and the AI agent extracts structured fields (HCP name, sentiment, topics, materials shared, etc.) and fills the form live. The rep can also correct or extend the log conversationally, and save the finished record to the database.

---

## Why an AI-first design?

Field reps spend a large share of their day on manual CRM data entry after a visit, which leads to sparse, delayed, or inconsistent logs. This module treats the LLM agent as the primary data-entry interface: the rep just talks about the visit the way they naturally would, and the agent turns that into structured CRM data — while still leaving the structured form fully visible and editable as a fallback.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Redux (state management), Vite |
| Backend | Python, FastAPI |
| AI Agent Framework | LangGraph |
| LLM | Groq API — `llama-3.1-8b-instant` (see note below) |
| Database | PostgreSQL (hosted on Supabase) |
| Font | Google Inter |

> **Note on the LLM model:** The task specification calls for Groq's `gemma2-9b-it`. As of this submission, Groq has **officially deprecated `gemma2-9b-it`**, recommending `llama-3.1-8b-instant` as the direct replacement ("delivers exceptional price-performance at the same speed"). This project uses `llama-3.1-8b-instant` accordingly. The model is fully configurable via the `GROQ_MODEL` environment variable, so it can be swapped back if `gemma2-9b-it` becomes available again.

---

## Project Structure

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

## The LangGraph Agent

### Role

The agent sits behind the `/chat` endpoint and acts as the intermediary between the rep's free-text description of an HCP visit and the structured `Interaction` record. On every message, it decides — using the LLM as a router — which tool(s) to call based on the conversation so far and the current form state, executes them, merges their results into the form, and replies to the rep in plain language confirming what changed.

The graph is a loop: **agent → (tools → apply_updates) → agent → END**, so the model can chain multiple tool calls in one turn (e.g. log the visit *and* suggest materials *and* schedule a follow-up in a single reply) before handing control back to the rep.

### The 5 Tools

1. **`log_interaction`** — Called the first time a visit is described. The LLM performs entity extraction directly through structured tool-calling: it reads the rep's natural-language description and extracts HCP name, interaction type, date, time, attendees, topics discussed, sentiment, outcomes, and follow-up actions as individual arguments, which are then merged into the form state.

2. **`edit_interaction`** — Called when the rep corrects or updates a single field on an already-logged interaction (e.g. *"actually the sentiment was negative"*). Takes a `field` + `value` pair and updates only that field, leaving the rest of the form untouched.

3. **`suggest_materials`** — Given the topics discussed, matches against a materials catalog (efficacy, safety, dosage, trial data, etc.) and adds relevant suggested materials to `materials_shared`.

4. **`schedule_followup`** — Given an action and a number of days out (default 14), computes a due date and appends a follow-up entry to `follow_up_actions` without overwriting any existing follow-ups.

5. **`summarize_hcp_history`** — Queries the database for prior logged interactions with the named HCP and summarizes sentiment trend and past outcomes, giving the rep context before logging today's visit.

---

## Setup & Run

### Prerequisites
- Python 3.11+
- Node.js 18+
- A Groq API key ([console.groq.com](https://console.groq.com))
- A PostgreSQL database (this project uses Supabase, but any Postgres instance works)

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
GROQ_MODEL=llama-3.1-8b-instant
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

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/chat` | Send a rep message + current form state + chat history; returns AI reply, updated form state, and list of tools invoked |
| POST | `/interactions` | Persist the current form state as a saved Interaction record |
| GET | `/interactions` | List all saved interactions |

---

## Known Limitations / Notes

- `date`/`time` are stored as plain strings rather than native `Date`/`Time` types, since the LLM naturally outputs them as text (`DD-MM-YYYY`, `HH:MM`).
- The form fields are read-only by design — all data entry happens through the AI chat panel, with a "Save Interaction" action to persist the current state.
- `gemma2-9b-it` was substituted with `llama-3.1-8b-instant` per Groq's own deprecation guidance (see note above).

---

## Author

Built as part of a technical assignment for an AI-First CRM HCP Module (Log Interaction Screen) task.