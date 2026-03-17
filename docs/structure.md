# VitaCompanion — Project Structure

```
Vita/
├── main.py                  # FastAPI app, router registration
├── db.py                    # Async SQLAlchemy session + Settings (pydantic-settings)
├── schema.sql               # Source of truth for DB schema
├── seed_rag.py              # Seeds 6 global wellness docs (idempotent)
├── prd.js                   # PRD generator — run: node prd.js
├── test.sh                  # End-to-end curl tests
├── models/
│   ├── user.py              # User, UserHealthProfile, UserPersonaConfig, DailyLog, UserSchedulerState
│   ├── log.py               # MealLog, WorkoutLog
│   └── conversation.py      # Conversation, Message
├── routers/
│   ├── users.py             # POST /users/onboard, GET /users/{id}
│   ├── logs.py              # POST /logs/daily|meal|workout, GET /logs/daily/{id}/{date}
│   ├── chat.py              # POST /chat (SSE streaming)
│   ├── scheduler.py         # POST /scheduler/checkin|nudge/{user_id}
│   └── reports.py           # GET /reports/weekly|monthly/{user_id}
├── services/
│   ├── user_service.py      # Onboarding — creates User + 3 related rows in one tx
│   ├── log_service.py       # Upsert daily log; meal logs auto-accumulate macros
│   ├── chat_service.py      # Context assembly, system prompt, Claude SSE streaming
│   ├── rag_service.py       # OpenAI ada-002 embeddings, pgvector cosine search
│   ├── report_service.py    # Weekly/monthly aggregation + Claude narrative + 24h cache
│   └── twilio_service.py    # WhatsApp via Twilio (failures never throw 500)
├── docs/
│   ├── schema.md            # Column gotchas, ENUMs, cast syntax, validation rules
│   └── structure.md         # This file
└── frontend/                # See frontend/CLAUDE.md
```

## Key Design Decisions
- Daily log uses **upsert** — safe to call multiple times per day
- Meal logs **auto-accumulate** macros into daily_log totals on insert
- RAG runs on every chat message; fails gracefully if OpenAI is down (returns [])
- Intent routing is inside the single Claude call — no separate detection step
- Safety override is always-on regardless of persona
- Scheduler endpoints are manually callable — pg_cron not yet activated
- Reports cached 24h by (user_id, period, period_start); DELETE row to bust cache

## Claude API Settings
- Model: `claude-sonnet-4-5`
- Chat: max_tokens=200, history window=last 6 messages, SSE via `AsyncAnthropic`
- Nudges: max_tokens=100
- Reports: max_tokens=150, plain text only
