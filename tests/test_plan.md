# VitaCompanion — Test Plan

**Backend:** http://localhost:8000
**Date context:** 2026-03-18
**Test user (no profile):** `9f6e1f8c-bf14-4e26-9497-836704795ab2` (test2@test.com)
**Test user (full profile):** `6ca8dacc-01d6-4985-81e0-74875113a346` (sharon@test.com)

---

## 1. User Onboarding — `POST /users/onboard`

| # | Scenario | Input | Expected |
|---|----------|-------|----------|
| 1.1 | New user | Full payload, unique email | 201, user_id returned, persona in response |
| 1.2 | Existing user (idempotent) | Same email/sso_id re-submitted | 201, same user_id, no duplicate rows |
| 1.3 | Vitals saved on users table | `date_of_birth`, `sex`, `height_cm` | Persisted in `users` table (not just health_profile) |
| 1.4 | Health profile created | First onboard | `user_health_profiles` row exists with `primary_goal`, `starting_weight_kg` |
| 1.5 | Persona config created | First onboard | `user_persona_configs` row exists with chosen persona |
| 1.6 | Scheduler state created | New user only | `user_scheduler_state` row exists |

**Regression (Bug #1):** Existing SSO user completing onboarding must have `date_of_birth`, `sex`, `height_cm` written to `users` table even when user row pre-existed.

---

## 2. User Lookup — `GET /users/by-email/{email}` + `GET /users/{user_id}`

| # | Scenario | Expected |
|---|----------|----------|
| 2.1 | by-email after onboard | 200, `has_profile: true` |
| 2.2 | by-email, user has no health_profile | 200, `has_profile: false` |
| 2.3 | by-email, user not found | 404 |
| 2.4 | by-id, valid user | 200, `full_name`, `email`, `onboarded_at` present |
| 2.5 | by-id, invalid UUID | 422 or 500 |
| 2.6 | by-id, unknown id | 404 |

---

## 3. Daily Logging — `POST /logs/daily` + `GET /logs/daily/{user_id}/{date}`

| # | Scenario | Input | Expected |
|---|----------|-------|----------|
| 3.1 | Create daily log | Valid payload | 201, `log_id` returned |
| 3.2 | Upsert same day | Second call same date | 201, same log updated (not duplicate) |
| 3.3 | Pain flag | `pain_reported: true` | `safety_flag_raised: true`, `flag_type: physical` |
| 3.4 | GET daily log | After POST | 200, all fields match |
| 3.5 | GET missing log | Date with no log | 404 |
| **Validation** | | | |
| 3.6 | Negative weight | `weight_kg: -5` | 422 |
| 3.7 | Sleep out of range | `sleep_hours: 25` | 422 |
| 3.8 | Sleep at boundary | `sleep_hours: 24` | 201 (valid) |

---

## 4. Meal Logging — `POST /logs/meal`

| # | Scenario | Input | Expected |
|---|----------|-------|----------|
| 4.1 | Log breakfast | Valid payload | 201, meal_log_id returned |
| 4.2 | Macro accumulation | Log 2 meals with calories | `daily_log.calories_total` = sum of both |
| 4.3 | Protein accumulation | Two meals with protein | `daily_log.protein_g` = sum |
| **Validation** | | | |
| 4.4 | Negative calories | `calories: -100` | 422 |
| 4.5 | Negative protein | `protein_g: -5` | 422 |

---

## 5. Workout Logging — `POST /logs/workout`

| # | Scenario | Input | Expected |
|---|----------|-------|----------|
| 5.1 | Log strength session | Valid payload | 201, `workout_log_id` returned |
| 5.2 | Daily log updated | After workout | `daily_log.workout_completed: true` |
| 5.3 | Pain during workout | `pain_during: true` | `daily_log.safety_flag_raised: true` |
| **Validation** | | | |
| 5.4 | Exertion = 0 | `perceived_exertion: 0` | 422 |
| 5.5 | Exertion = 11 | `perceived_exertion: 11` | 422 |
| 5.6 | Exertion = 10 | `perceived_exertion: 10` | 201 (valid boundary) |

---

## 6. Chat — `POST /chat`

| # | Scenario | Input | Expected |
|---|----------|-------|----------|
| 6.1 | Valid message, profiled user | Non-empty message | SSE stream with `data: {"chunk": "..."}` lines |
| 6.2 | Stream completes | — | `data: {"done": true, "conversation_id": "..."}` event |
| 6.3 | Conversation continuity | `conversation_id` passed | Same conversation extended |
| 6.4 | No profile user | `user_id` with no health_profile | 500 (raised before streaming) |
| **Validation** | | | |
| 6.5 | Empty message | `"message": ""` | 422 |
| 6.6 | Whitespace message | `"message": "   "` | 422 |

**Regression (Bug #2):** Age calculation uses `(date.today() - date_of_birth).days // 365`, not naive year subtraction. Must not crash when `date_of_birth` is NULL.

---

## 7. Scheduler — `POST /scheduler/checkin/{user_id}` + `/nudge/{user_id}`

| # | Scenario | Expected |
|---|----------|----------|
| 7.1 | Checkin for profiled user | 200, `message` field non-empty |
| 7.2 | Nudge for profiled user | 200, `message` field non-empty |
| 7.3 | Twilio failure | 200, `whatsapp_sent: false` (never 500) |
| 7.4 | Unknown user_id | 404 |
| 7.5 | Retry on Claude overload | Max 3 retries at 1s/2s/4s backoff |

---

## 8. Reports — `GET /reports/weekly/{user_id}` + `/monthly/{user_id}`

| # | Scenario | Expected |
|---|----------|----------|
| 8.1 | Weekly report | 200, `narrative` field non-empty |
| 8.2 | Monthly report | 200, `narrative` field non-empty |
| 8.3 | Cache hit (2nd request same day) | 200, same result, no new Claude call |
| 8.4 | Unknown user_id | 404 |

---

## 9. Persona Switch — `POST /users/{user_id}/persona/switch`

| # | Scenario | Input | Expected |
|---|----------|-------|----------|
| 9.1 | Switch to commander | `{"persona": "commander"}` | 200, `active_persona: commander`, `previous_persona` set |
| 9.2 | Log entry created | Any switch | Row in `persona_switch_log` table |
| 9.3 | Verify via by-email | After switch | `persona` field in sync response updated |
| 9.4 | Invalid persona | `{"persona": "drill_sergeant"}` | 422 |
| 9.5 | Unknown user_id | — | 404 |

---

## 10. Auth Sync — `POST /api/auth/sync` (frontend route)

| # | Scenario | Expected |
|---|----------|----------|
| 10.1 | Authenticated user with profile | `{ user_id, full_name, has_profile: true }` |
| 10.2 | Authenticated user without profile | `{ has_profile: false }` → frontend redirects to /onboarding |
| 10.3 | User not in DB | 404 → frontend redirects to /onboarding |
| 10.4 | Unauthenticated | 401 |

---

## 11. End-to-End Redirect Flow

| # | Scenario | Expected |
|---|----------|----------|
| 11.1 | New SSO user visits /dashboard | Redirect to /onboarding |
| 11.2 | New SSO user visits /chat | Redirect to /onboarding |
| 11.3 | After onboarding completes | Redirect to /dashboard |
| 11.4 | User with profile visits /dashboard | Dashboard loads, name shows |

---

## Test Data Summary

| Resource | Value |
|----------|-------|
| Test email (e2e script) | `e2e-{timestamp}@vitacompanion.test` |
| No-profile user | `9f6e1f8c-bf14-4e26-9497-836704795ab2` |
| Full-profile user | `6ca8dacc-01d6-4985-81e0-74875113a346` |
| Test date | `2026-03-18` |
