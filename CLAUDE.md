# VitaCompanion — Claude Code Context

AI wellness coaching platform for adults 50+. FastAPI backend + Next.js frontend.

## Servers
```bash
# Backend (terminal 1)
cd ~/Downloads/Vita && source venv/bin/activate && uvicorn main:app --reload

# Frontend (terminal 2)
cd ~/Downloads/Vita/frontend && npm run dev
```
Backend: http://localhost:8000 | Frontend: http://localhost:3000

## Database
PostgreSQL: `vitacompanion` | Re-seed RAG: `python seed_rag.py`

**Test user**
```
id:    9f6e1f8c-bf14-4e26-9497-836704795ab2
email: test2@test.com  lang: en
```

## Critical Gotchas
1. `users.full_name` — NOT `users.name`
2. `rag_documents` has no `title`/`category` — use `doc_type` and `metadata->>'title'`
3. Never pass `created_at`/`updated_at` to `Conversation()` constructor — DB sets them
4. asyncpg: use `CAST(:p AS vector)` not `:p::vector` (breaks `$N` substitution)
5. All ENUMs need `create_type=False` — see `docs/schema.md` for full list

## What's Left to Build
- [x] Day 9: Google SSO wired to real users, POST /persona/switch
- [x] Day 10: Fix markdown rendering in chat (react-markdown)
- [x] Day 10: Hosting prep (Procfile, .env.example, README.md, requirements.txt)
- [x] Day 11: pg_cron activation (pg_cron_setup.sql + scheduler_worker.py + docs)
- [x] Day 11: Polish — Today's Log page (/log), onboarding page (/onboard), real name on dashboard, persona flicker fix, onboard redirect for new SSO users
- [x] Day 11: Multi-step onboarding flow at /onboarding (goal → vitals → medical → dietary → persona)
- [x] Day 11: End-to-end test suite (tests/test_e2e.sh — 69 assertions, all pass)
- [x] Day 11: Bug fixes — date_of_birth not saved for existing SSO users; chat 200→404 for missing profile; GET /users/{id} lazy-load 500; DOB in system prompt
- [ ] Day 12: Deploy backend to Railway/Render, frontend to Vercel
- [ ] Day 12: Set up real Twilio number (move off sandbox)
- [ ] Day 12: Activate pg_cron on hosted PostgreSQL DB
- [ ] Day 12: End-to-end smoke test on production

## Docs
- `docs/schema.md` — column names, ENUMs, cast syntax, validation rules
- `docs/structure.md` — full file tree, design decisions, Claude API settings
- `frontend/CLAUDE.md` — frontend-specific context
- `schema.sql` — source of truth for DB schema
