# VitaCompanion — Manual Frontend Onboarding Test Checklist

**URL:** http://localhost:3000/onboarding
**Prerequisites:** Frontend and backend both running. Signed in as a Google user who has NO health profile yet (or use a fresh incognito session with a test Google account).

---

## Pre-test Setup

- [ ] Backend running: `uvicorn main:app --reload` (http://localhost:8000)
- [ ] Frontend running: `npm run dev` (http://localhost:3000)
- [ ] In the database, confirm the test user has no health profile:
  ```sql
  SELECT u.email, hp.id FROM users u
  LEFT JOIN user_health_profiles hp ON hp.user_id = u.id
  WHERE u.email = '<your-test-email>';
  ```
  Expected: `hp.id` is NULL

---

## TC-01: Redirect to /onboarding for user without profile

**Steps:**
1. Sign in via Google SSO (or navigate to http://localhost:3000)
2. Navigate to http://localhost:3000/dashboard

**Expected:**
- [ ] Automatically redirected to `/onboarding` without showing the dashboard
- [ ] URL in browser is now `/onboarding`

---

## TC-02: Step 1 — Goal selection

**Steps:**
1. Observe the onboarding page loads
2. Confirm 5 goal options are shown: Lose weight, Build muscle, General health, Improve endurance, Maintain weight
3. Click "Build muscle"

**Expected:**
- [ ] Step indicator shows step 1 of 5 active (first bar lit)
- [ ] "Build muscle" card is highlighted in blue
- [ ] "Continue" button is enabled
- [ ] Clicking "Continue" advances to step 2

---

## TC-03: Step 2 — Vitals (required fields validation)

**Steps:**
1. On step 2, click "Continue" WITHOUT filling any fields

**Expected:**
- [ ] "Continue" button is disabled (greyed out) — date_of_birth, height_cm, starting_weight_kg are all required

**Steps (continued):**
2. Fill in:
   - Date of birth: `1971-04-12` (use date picker)
   - Sex: Female
   - Height (cm): `166`
   - Weight (kg): `68`
   - Activity level: click "Moderate"
3. Click "Continue"

**Expected:**
- [ ] Continue button is now enabled after all 3 required fields are filled
- [ ] Advances to step 3

---

## TC-04: Step 3 — Medical (optional, skip)

**Steps:**
1. Leave both fields blank
2. Click "Skip" (button should say "Skip" not "Continue")

**Expected:**
- [ ] Advances to step 4 without error

**Optional — fill and verify:**
- [ ] Enter `type2_diabetes, hypertension` in Medical conditions
- [ ] Enter `metformin` in Medications
- [ ] Confirm comma-separated values are accepted

---

## TC-05: Step 4 — Dietary (optional, skip)

**Steps:**
1. Leave blank, click "Skip"

**Expected:**
- [ ] Advances to step 5

---

## TC-06: Step 5 — Persona selection + submit

**Steps:**
1. Select "Coach" persona
2. Click "Get started"

**Expected:**
- [ ] Button changes to "Setting up your account…" while submitting
- [ ] No error message appears
- [ ] Redirected to `/dashboard` after ~1-2 seconds

---

## TC-07: Dashboard loads correctly after onboarding

**After redirect to /dashboard:**

- [ ] User's first name appears in the header ("Welcome back, [Name]!")
- [ ] Two cards visible: "Chat with Coach" and "Today's Log"
- [ ] No redirect loop back to /onboarding

---

## TC-08: DB verification after onboarding

Run these queries after completing TC-06:

```sql
-- Users table — should have date_of_birth and sex populated
SELECT full_name, date_of_birth, sex, height_cm
FROM users WHERE email = '<your-test-email>';
```
- [ ] `date_of_birth` = `1971-04-12`
- [ ] `sex` = `female`
- [ ] `height_cm` = `166`

```sql
-- Health profile should exist
SELECT primary_goal, starting_weight_kg, activity_level
FROM user_health_profiles
WHERE user_id = (SELECT id FROM users WHERE email = '<your-test-email>');
```
- [ ] `primary_goal` = `muscle_gain`
- [ ] `starting_weight_kg` = `68`
- [ ] `activity_level` = `moderate`

```sql
-- Persona config
SELECT active_persona FROM user_persona_configs
WHERE user_id = (SELECT id FROM users WHERE email = '<your-test-email>');
```
- [ ] `active_persona` = `coach`

---

## TC-09: Onboarding is idempotent (submit twice)

**Steps:**
1. Navigate back to `/onboarding` manually
2. Complete the form again with slightly different values (e.g., weight = 70)
3. Submit

**Expected:**
- [ ] Returns to `/dashboard` (no error)
- [ ] Same user_id is used (no duplicate user row)
- [ ] `has_profile` is still true after re-onboarding

---

## TC-10: Chat redirect guard

**Steps:**
1. Log out (click "Sign out")
2. Sign back in with the same Google account
3. Navigate directly to `/chat`

**Expected (user now HAS profile):**
- [ ] Chat page loads normally (no redirect to /onboarding)

**To test the guard:**
1. Delete the health_profile row in the DB manually:
   ```sql
   DELETE FROM user_health_profiles
   WHERE user_id = (SELECT id FROM users WHERE email = '<your-test-email>');
   ```
2. Navigate to `/chat`
- [ ] Redirected to `/onboarding`

---

## TC-11: Back navigation

**Steps:**
1. Start onboarding, advance to step 3
2. Click "Back"

**Expected:**
- [ ] Returns to step 2 with previously entered values preserved (form state retained)
- [ ] Step indicator correctly reflects current step

---

## TC-12: Error handling — backend down

**Steps:**
1. Stop the backend (`Ctrl+C` in the uvicorn terminal)
2. Complete onboarding and click "Get started"

**Expected:**
- [ ] Error message appears: should show something meaningful (not just "Something went wrong." if possible — at minimum the catch path displays a message)
- [ ] Button re-enables after failure so user can retry

---

## Pass Criteria Summary

| Test | Status |
|------|--------|
| TC-01: Redirect for no-profile user | ☐ |
| TC-02: Step 1 goal selection | ☐ |
| TC-03: Step 2 vitals validation | ☐ |
| TC-04: Step 3 medical (skip) | ☐ |
| TC-05: Step 4 dietary (skip) | ☐ |
| TC-06: Step 5 persona + submit | ☐ |
| TC-07: Dashboard loads after onboarding | ☐ |
| TC-08: DB verification | ☐ |
| TC-09: Idempotency | ☐ |
| TC-10: Chat redirect guard | ☐ |
| TC-11: Back navigation preserves state | ☐ |
| TC-12: Error handling — backend down | ☐ |
