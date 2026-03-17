# VitaCompanion

AI wellness coaching platform for adults 50+. Streaming chat, daily logging, WhatsApp nudges, and weekly reports — all voiced through a persona the user picks.

**Stack:** FastAPI + PostgreSQL (pgvector) + Next.js 14

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| PostgreSQL | 15+ with [pgvector](https://github.com/pgvector/pgvector) |

---

## Backend setup

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd Vita

# 2. Create and activate a virtualenv
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create the database
createdb vitacompanion
psql vitacompanion < schema.sql  # creates all tables, enums, indexes

# 5. Copy and fill in environment variables
cp .env.example .env
# Edit .env with your real keys

# 6. (Optional) Seed the RAG knowledge base
python seed_rag.py

# 7. Start the backend
uvicorn main:app --reload
```

Backend runs at **http://localhost:8000** — docs at `/docs`.

---

## Frontend setup

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Copy and fill in environment variables
cp .env.example .env.local
# Edit .env.local with your real keys

# 3. Start the dev server
npm run dev
```

Frontend runs at **http://localhost:3000**.

---

## Environment variables

See [.env.example](.env.example) (backend) and [frontend/.env.example](frontend/.env.example) (frontend) for the full list with descriptions.

**Minimum required to run locally:**

| Variable | Where | Purpose |
|----------|-------|---------|
| `DATABASE_URL` | `.env` | PostgreSQL connection |
| `ANTHROPIC_API_KEY` | `.env` | Chat + nudge generation |
| `NEXTAUTH_SECRET` | `frontend/.env.local` | Session signing |
| `NEXT_PUBLIC_API_URL` | `frontend/.env.local` | Backend URL |

Google OAuth and Twilio are optional for local dev — the "Continue as test user" link on the landing page bypasses SSO.

---

## Test user

A seeded test user is available without needing to run the full onboarding flow:

```
id:    9f6e1f8c-bf14-4e26-9497-836704795ab2
email: test2@test.com
```

---

## Deployment (Railway / Render)

**Backend**

1. Set all variables from `.env.example` in the platform's env UI.
2. The `Procfile` is already configured:
   ```
   web: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
3. Add a PostgreSQL plugin and point `DATABASE_URL` at it. Run `schema.sql` once after provisioning.

**Frontend**

Deploy as a Next.js app (Vercel is the easiest). Set variables from `frontend/.env.example`, pointing `NEXT_PUBLIC_API_URL` at the deployed backend.

---

## Key docs

- [`docs/schema.md`](docs/schema.md) — DB column names, ENUMs, asyncpg cast syntax
- [`docs/structure.md`](docs/structure.md) — full file tree and design decisions
- [`frontend/CLAUDE.md`](frontend/CLAUDE.md) — frontend-specific context
- [`schema.sql`](schema.sql) — source of truth for the database schema
