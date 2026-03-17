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
- [ ] Day 11: pg_cron activation (uncomment cron stubs in schema.sql, wire to scheduler endpoints)
- [ ] Day 11: End-to-end polish (onboarding flow, error pages, loading states)

## Docs
- `docs/schema.md` — column names, ENUMs, cast syntax, validation rules
- `docs/structure.md` — full file tree, design decisions, Claude API settings
- `frontend/CLAUDE.md` — frontend-specific context
- `schema.sql` — source of truth for DB schema
