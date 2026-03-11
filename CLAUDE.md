# VitaCompanion — Claude Code Context

## What This Is
AI wellness coaching platform for adults 50+. Python/FastAPI backend + Next.js frontend.
Backend: `~/Downloads/Vita/` | Frontend: `~/Downloads/Vita/frontend/`

## Servers
```bash
# Backend (terminal 1)
cd ~/Downloads/Vita && source venv/bin/activate && uvicorn main:app --reload

# Frontend (terminal 2)
cd ~/Downloads/Vita/frontend && npm run dev
```
Backend: http://localhost:8000 | Frontend: http://localhost:3000

## Database
PostgreSQL database: `vitacompanion`
```bash
psql vitacompanion        # connect
python seed_rag.py        # re-seed RAG docs (idempotent)
```

### Test User
```
id:    9f6e1f8c-bf14-4e26-9497-836704795ab2
name:  Test User
email: test2@test.com
lang:  en
```

## Project Structure
```
Vita/
├── main.py                  # FastAPI app, router registration
├── db.py                    # Async SQLAlchemy session
├── schema.sql               # Source of truth for DB schema
├── seed_rag.py              # Seeds 6 global wellness docs
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
│   └── scheduler.py         # POST /scheduler/checkin|nudge/{user_id}
├── services/
│   ├── user_service.py
│   ├── log_service.py       # Includes input validation (no negative values)
│   ├── chat_service.py      # Context assembly, system prompt, Claude streaming
│   ├── rag_service.py       # OpenAI ada-002 embeddings, pgvector cosine search
│   ├── twilio_service.py    # WhatsApp via Twilio
│   └── nutrition_service.py / training_service.py  # Specialist bots (merged into chat)
└── frontend/
    ├── app/
    │   ├── page.tsx          # Landing
    │   ├── chat/page.tsx     # Chat UI (SSE streaming, DEV_USER_ID hardcoded)
    │   └── dashboard/page.tsx
    └── components/
        └── ChatMessage.tsx
```

## Critical Schema Facts
**Do not rename these — they differ from the original design:**
- `users.full_name` (not `name`)
- `rag_documents` has NO `title` or `category` columns
  - Use `doc_type` (text) for category
  - Use `metadata` (jsonb) for title: `metadata->>'title'`
- `Conversation` SQLAlchemy model: do NOT pass `created_at` or `updated_at` to constructor — set by DB default

**All custom ENUMs must use:**
```python
Column(ENUM('val1','val2', name='type_name', create_type=False))
```

**ENUM values in use:**
- `persona_style`: friend, coach, commander
- `bot_type`: orchestrator, nutrition, training, reporting, scheduler
- `message_role`: user, assistant, system
- `flag_type`: none, physical, emotional, constraint_violation, ...
- `session_type`: cardio, strength, mobility, rest, active_recovery
- `intensity_level`: low, moderate, moderate_high, high

## Claude API Settings
- Model: `claude-sonnet-4-5`
- max_tokens: 200
- History window: last 6 messages
- System prompt rule: "IMPORTANT: Reply in 2-3 sentences maximum. Be direct. No lists unless explicitly asked."
- Streaming: SSE via `AsyncAnthropic` + `client.messages.stream()`
- RAG: top-3 docs, 300 char snippets, fails gracefully if OpenAI is down

## Key Design Decisions
- Daily log uses **upsert** — safe to call multiple times per day
- Meal logs **auto-accumulate** macros into daily_log totals on insert
- RAG retrieval runs on every chat message (OpenAI ada-002, cosine distance)
- Intent routing is handled **inside** the single Claude call via system prompt — no separate intent detection call
- Safety override is always-on regardless of persona
- Scheduler endpoints are manually callable — pg_cron not yet activated
- WhatsApp send failures return `whatsapp_sent: false` — never throw 500

## Validation Rules (enforced in log_service.py)
- `weight_kg >= 0`
- `0 <= sleep_hours <= 24`
- `calories, protein_g, fat_g, carbs_g >= 0`
- `1 <= perceived_exertion <= 10`
- Chat message: non-empty, non-whitespace (422 before any DB call)
- Missing health_profile or persona_config: raises 404 before streaming starts

## What's Left to Build
- [ ] Day 8: Reporting engine (GET /reports/weekly|monthly)
- [ ] Day 9: Google SSO wired to real users (replace DEV_USER_ID in frontend)
- [ ] Day 9: POST /persona/switch endpoint
- [ ] Day 10: pg_cron jobs activation, hosting prep, end-to-end polish

## PRD
Update after each day: edit `prd.js` then run `node prd.js` → regenerates `VitaCompanion_PRD.docx`
