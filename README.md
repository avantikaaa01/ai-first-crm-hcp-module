# AI-First CRM — HCP Module: Log Interaction Screen

A field-rep facing "Log Interaction" screen for a pharma CRM's Healthcare
Professional (HCP) module. Reps can log a visit either through a structured
form or by describing it in plain language to a LangGraph agent, which
extracts and saves structured data via tool calls, live, in front of the rep.

## Why it's built this way

Field reps are between hospital visits, on their phone, with two minutes to
spare. A ten-field form is friction. But compliance and pipeline reporting
need structured, consistent data. The conversational path and the form path
both funnel through the **same `log_interaction` tool**, so however the rep
logs it, the record that lands in the database is identical in shape — one
source of truth, two doors in.

## Architecture

```
frontend/  React + Redux Toolkit
  ├─ StructuredForm     -> POST /api/interactions/form
  ├─ ChatInterface      -> POST /api/chat/            (talks to the LangGraph agent)
  └─ redux slices for hcps, interactions, chat session state

backend/   FastAPI + LangGraph + Groq
  ├─ routers/hcp.py           HCP CRUD
  ├─ routers/interactions.py  structured-form entry point (reuses agent tools directly)
  ├─ routers/chat.py          conversational entry point (runs the LangGraph agent)
  ├─ agent/graph.py           the LangGraph ReAct loop (agent node <-> tools node)
  ├─ agent/tools.py           the 5 tools (see below)
  ├─ agent/llm.py             Groq client (gemma2-9b-it primary, llama-3.3-70b-versatile fallback)
  └─ models.py                SQLAlchemy models (HCP, Interaction) — Postgres/MySQL/SQLite
```

## Role of the LangGraph agent

The agent is the single decision-maker between a rep's free-text description
and the structured CRM record. It doesn't just summarize — it decides *which*
tool(s) a message calls for (log a new visit? edit an old one? check history
before responding? flag a compliance risk?), calls them, and reports back in
plain language. The graph is a standard ReAct loop:

```
START -> agent (LLM reasons, may emit tool_calls)
           |
           v
        tools (execute; results appended to conversation)
           |
           v
        agent (sees tool results, may call more tools or respond in text)
           |
           v
          END (once it responds without further tool calls)
```

Keeping the loop tool-call-driven (rather than one giant prompt) means each
DB write is auditable — a compliance reviewer can see exactly which tool ran
with which arguments, not just trust a paragraph the LLM wrote.

## The 6 tools

| Tool | Purpose |
|---|---|
| **`log_interaction`** | Takes free-text notes + hcp_id. Calls the LLM once with a strict JSON-extraction prompt to produce: a 2–3 sentence summary, interaction type, sentiment, `topics_discussed` (entity extraction over product/topic mentions), `samples_distributed`, and whether a follow-up is implied. Writes the row to the DB and returns a compact confirmation. |
| **`edit_interaction`** | Takes an `interaction_id` and a `changes` dict. If the rep is correcting the underlying notes, it re-runs the same extraction so the summary/topics stay consistent with the new text rather than going stale; otherwise it patches only the fields given. |
| **`search_hcp`** | Resolves a doctor's name/specialty/hospital mentioned in chat to an actual `hcp_id`. The agent calls this whenever a rep names a doctor without UI context providing the id, and before `log_interaction` if it doesn't already know who it's logging for. |
| **`get_hcp_history`** | Pulls the HCP's last N interactions (summaries + topics). The agent calls this before answering questions like "what did we talk about last time" or before logging, to avoid the LLM inventing context it doesn't have. |
| **`schedule_followup`** | Sets `follow_up_required` + `follow_up_date` on an interaction from a natural date reference ("follow up in 2 weeks"). |
| **`check_compliance`** | Runs interaction text through a second, narrowly-scoped LLM prompt that flags off-label claims, unsubstantiated efficacy language, or sample-quantity concerns — a pharma-specific guardrail, since HCP interaction logs are audited. |

`log_interaction` and `edit_interaction` are the two mandatory tools.
`search_hcp`, `get_hcp_history`, and `schedule_followup` are the three
named example tools from the brief. `check_compliance` goes one beyond
the minimum of 5 — a regulatory guardrail specific to pharma HCP logs.

## Running it

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # then paste your Groq API key from console.groq.com/keys
python seed.py          # creates 3 demo HCPs
uvicorn app.main:app --reload --port 8000
```
API docs at `http://localhost:8000/docs`.

By default it uses local SQLite (`hcp_crm.db`) so there's zero setup to try
it. For Postgres/MySQL, set `DATABASE_URL` in `.env`, e.g.
`postgresql+psycopg2://user:pass@localhost:5432/hcp_crm`.

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Opens at `http://localhost:5173`. It expects the backend at
`http://localhost:8000` (override with a `VITE_API_BASE` env var).

## Try the conversational flow

Pick an HCP on the left, switch to "Conversational", and try:

> Met Dr. Mehta today, she was really happy with the CardioFlex trial data
> and wants 20 more samples. Follow up in 2 weeks.

Watch the "Agent activity" panel — you'll see `log_interaction` (and
`schedule_followup`) fire with their structured output, in real time,
before the agent's plain-language reply lands in the chat.

## What's stubbed vs. production-ready

This is a Round 1 technical scaffold, not a shipped product. Things I'd
harden for production: session storage for chat (currently in-memory per
process — needs Redis for multi-worker deployments), auth/RBAC for reps vs.
managers, retry/backoff around the Groq calls, and a proper migrations setup
(Alembic) instead of `create_all`.
