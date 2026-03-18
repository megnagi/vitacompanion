# VitaCompanion — Session Handoff
_Last updated: 2026-03-18 (end of Day 11)_

---

## Dev Environment — Start Commands

```bash
# 1. Backend
cd ~/Downloads/Vita
source venv/bin/activate
uvicorn main:app --reload
# → http://localhost:8000   (API docs at /docs)

# 2. Frontend
cd ~/Downloads/Vita/frontend
npm run dev
# → http://localhost:3000

# 3. Database
psql vitacompanion          # connect
python seed_rag.py          # re-seed RAG docs if needed (idempotent)

# 4. Run end-to-end tests (backend must be running)
cd ~/Downloads/Vita
bash tests/test_e2e.sh      # 69 assertions, ~60s
```

---

## Feature Status

### ✅ Working

| Feature | Notes |
|---------|-------|
| Google SSO sign-in | next-auth v4 Google provider; callback creates user row if new |
| Onboarding flow `/onboarding` | 5-step form (goal → vitals → medical → dietary → persona); upserts existing users correctly |
| Has-profile redirect | `/dashboard` and `/chat` redirect to `/onboarding` when `has_profile: false` |
| Chat with SSE streaming | `POST /chat` → `text/event-stream`; chunks arrive in real time |
| RAG context | Top-3 docs injected into every system prompt via pgvector cosine search |
| Persona switching | `POST /users/{id}/persona/switch`; persists to DB + logs to `persona_switch_log` |
| Daily logging | Upsert; pain flag raises `safety_flag_raised` |
| Meal logging | Macros auto-accumulate into `daily_log` totals |
| Workout logging | Sets `workout_completed`; pain flag cascades to daily_log |
| Scheduler checkin/nudge | Claude-generated messages; Twilio WhatsApp (sandbox); retry on overload |
| Weekly + monthly reports | Claude narrative; 24h cache in `reports` table |
| Today's Log page `/log` | Form for daily weight, sleep, energy, mood, notes |
| Dashboard | Shows first name, date, links to chat and log |
| Markdown rendering | `react-markdown` in `ChatMessage.tsx` |
| Age in system prompt | `(date.today() - dob).days // 365`; null-safe |
| DOB in system prompt | `DOB: {date_of_birth}` included in user context line |
| Test suite | `tests/test_e2e.sh` — 69 assertions across all endpoints |

---

### ⏳ Not Yet Done (Day 12)

| Item | Detail |
|------|--------|
| Production deploy | Railway/Render for backend; Vercel for frontend; env vars to configure |
| Real Twilio number | Currently on sandbox (messages only go to verified numbers) |
| pg_cron on hosted DB | `pg_cron_setup.sql` is written; needs to run on the hosted Postgres instance |
| Production smoke test | Run `test_e2e.sh` with `BASE=https://your-backend.railway.app` |

---

## Known Rough Edges

| Issue | Location | Notes |
|-------|----------|-------|
| `test2@test.com` has no health_profile | DB | Intentional fixture for edge-case tests — do not onboard it |
| E2E test users accumulate in DB | `users` table | 3 `e2e-*@vita-e2e.dev` rows from test runs; safe to delete |
| Report 24h cache | `reports` table | If narrative seems stale, `DELETE FROM reports WHERE user_id = '...'` to bust |
| Twilio sandbox | `services/twilio_service.py` | Scheduler returns `whatsapp_sent: false` for non-verified numbers; not a bug |
| `sharon.magen@gmail.com` persona = `coach` | DB | Can be switched via `POST /users/{id}/persona/switch` or the chat UI |
| No logout redirect to `/` | frontend | `signOut({callbackUrl: "/"})` is present in dashboard but not chat page |
| Onboarding skips `allergies` field | `user_service.py` | Payload sends `dietary_restrictions` but not `allergies`; fine for now |

---

## DB State (2026-03-18)

### `users` table

| id | email | full_name | date_of_birth | has_profile | persona |
|----|-------|-----------|---------------|-------------|---------|
| `6ca8dacc-01d6-4985-81e0-74875113a346` | sharon@test.com | Sharon Magen | 1975-06-15 | ✅ | friend |
| `9f6e1f8c-bf14-4e26-9497-836704795ab2` | test2@test.com | Test User | 1974-01-01 | ❌ | friend |
| `63e98eb5-3798-48a4-a3fe-8eaf5c9409cb` | sharon.magen@gmail.com | Sharon Magen | 1974-02-16 | ✅ | coach |
| `b7dbd504-...` | e2e-1773822697@vita-e2e.dev | E2E Test User | 1975-06-20 | ✅ | friend |
| `077b2d97-...` | e2e-1773823112@vita-e2e.dev | E2E Test User | 1975-06-20 | ✅ | friend |
| `91a5973c-...` | e2e-1773823751@vita-e2e.dev | E2E Test User | 1975-06-20 | ✅ | friend |

**Primary user for manual testing:** `sharon.magen@gmail.com` (`63e98eb5-3798-48a4-a3fe-8eaf5c9409cb`)

### Useful queries

```sql
-- Check a user's full profile
SELECT u.email, u.date_of_birth, u.sex, u.height_cm,
       hp.primary_goal, hp.starting_weight_kg, hp.activity_level,
       pc.active_persona
FROM users u
LEFT JOIN user_health_profiles hp ON hp.user_id = u.id
LEFT JOIN user_persona_configs pc ON pc.user_id = u.id
WHERE u.email = 'sharon.magen@gmail.com';

-- Today's log for a user
SELECT * FROM daily_logs
WHERE user_id = '63e98eb5-3798-48a4-a3fe-8eaf5c9409cb'
  AND log_date = CURRENT_DATE;

-- Bust report cache
DELETE FROM reports WHERE user_id = '63e98eb5-3798-48a4-a3fe-8eaf5c9409cb';

-- Delete e2e test users (safe to run anytime)
DELETE FROM users WHERE email LIKE 'e2e-%@vita-e2e.dev';
```

---

## Key File Locations

| What | Where |
|------|-------|
| Backend entry point | `main.py` |
| DB schema (source of truth) | `schema.sql` |
| System prompt + age calc | `services/chat_service.py:56-101` |
| Onboarding service (vitals save fix) | `services/user_service.py:117-127` |
| Chat router (pre-validation fix) | `routers/chat.py:23-42` |
| Sync route (has_profile) | `frontend/app/api/auth/sync/route.ts` |
| Onboarding page | `frontend/app/onboarding/page.tsx` |
| End-to-end tests | `tests/test_e2e.sh` |
| Schema reference | `docs/schema.md` |
| Project structure | `docs/structure.md` |

---

## Day 12 Deploy Checklist

```
Backend (Railway / Render)
  [ ] Set env vars: ANTHROPIC_API_KEY, DATABASE_URL, TWILIO_*, OPENAI_API_KEY
  [ ] Run: psql $DATABASE_URL < schema.sql
  [ ] Run: python seed_rag.py
  [ ] Enable pg_cron: psql $DATABASE_URL < pg_cron_setup.sql
  [ ] Verify: curl https://your-backend.railway.app/docs

Frontend (Vercel)
  [ ] Set NEXTAUTH_URL = https://your-frontend.vercel.app
  [ ] Set NEXTAUTH_SECRET (random 32-byte string)
  [ ] Set GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET
  [ ] Set NEXT_PUBLIC_API_URL = https://your-backend.railway.app
  [ ] Add Vercel domain to Google OAuth authorised redirect URIs

Smoke test
  [ ] BASE=https://your-backend.railway.app bash tests/test_e2e.sh
```
