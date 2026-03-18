#!/usr/bin/env bash
# tests/test_e2e.sh — VitaCompanion end-to-end backend tests
# Usage: ./tests/test_e2e.sh
# Requires: curl, jq, psql

BASE="${BASE:-http://localhost:8000}"
TODAY="2026-03-18"

# Fixed test identifiers — deterministic across runs
TIMESTAMP=$(date +%s)
TEST_EMAIL="e2e-${TIMESTAMP}@vita-e2e.dev"
TEST_SSO="e2e_sso_${TIMESTAMP}"

# Existing users in the DB
PROFILED_USER_ID="6ca8dacc-01d6-4985-81e0-74875113a346"  # sharon@test.com — full profile
NO_PROFILE_USER_ID="9f6e1f8c-bf14-4e26-9497-836704795ab2" # test2@test.com  — no health_profile

PASS=0; FAIL=0
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'

pass()    { PASS=$((PASS+1)); printf "${GREEN}  ✓ PASS${NC} %s\n" "$1"; }
fail()    { FAIL=$((FAIL+1)); printf "${RED}  ✗ FAIL${NC} %s — %s\n" "$1" "$2"; }
section() { printf "\n${BOLD}${YELLOW}── %s ──${NC}\n" "$1"; }

# curl: returns BODY\nSTATUS_CODE
vcurl() { curl -s -w "\n%{http_code}" "$@"; }

status_of() { printf '%s' "$1" | tail -n1; }
body_of()   { printf '%s' "$1" | sed '$d'; }

check_status() {
    local label="$1" expected="$2" resp="$3"
    local actual; actual=$(status_of "$resp")
    if [ "$actual" = "$expected" ]; then
        pass "$label → HTTP $actual"
    else
        fail "$label" "expected HTTP $expected, got $actual — $(body_of "$resp" | head -c 200)"
    fi
}

check_field() {
    local label="$1" field="$2" expected="$3" body="$4"
    local actual; actual=$(printf '%s' "$body" | jq -r "$field" 2>/dev/null)
    if [ "$actual" = "$expected" ]; then
        pass "$label ($field = $actual)"
    else
        fail "$label" "$field: expected '$expected', got '$actual'"
    fi
}

check_truthy() {
    local label="$1" field="$2" body="$3"
    local actual; actual=$(printf '%s' "$body" | jq -r "$field" 2>/dev/null)
    if [ -n "$actual" ] && [ "$actual" != "null" ] && [ "$actual" != "false" ] && [ "$actual" != "" ]; then
        pass "$label ($field = ${actual:0:60})"
    else
        fail "$label" "$field not truthy (got: '$actual')"
    fi
}

# ─── Pre-flight ────────────────────────────────────────────────────
section "Pre-flight"

if ! command -v jq &>/dev/null; then
    printf "${RED}jq is required but not installed. Run: brew install jq${NC}\n"; exit 1
fi
pass "jq available"

if ! command -v psql &>/dev/null; then
    printf "${YELLOW}  ⚠ psql not found — DB verification steps will be skipped${NC}\n"
    HAS_PSQL=0
else
    HAS_PSQL=1
    pass "psql available"
fi

HEALTH_RESP=$(vcurl "$BASE/docs" 2>/dev/null)
HEALTH_STATUS=$(status_of "$HEALTH_RESP")
if [ "$HEALTH_STATUS" = "200" ]; then
    pass "Backend reachable at $BASE"
else
    printf "${RED}Backend not reachable at $BASE (HTTP $HEALTH_STATUS). Is uvicorn running?${NC}\n"
    exit 1
fi

# ─── 1. Onboarding — new user ──────────────────────────────────────
section "1. POST /users/onboard — new user"

ONBOARD_RESP=$(vcurl -X POST "$BASE/users/onboard" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"$TEST_EMAIL\",
        \"full_name\": \"E2E Test User\",
        \"sso_provider\": \"google\",
        \"sso_id\": \"$TEST_SSO\",
        \"date_of_birth\": \"1975-06-20\",
        \"sex\": \"female\",
        \"height_cm\": 168.0,
        \"starting_weight_kg\": 70.0,
        \"primary_goal\": \"weight_loss\",
        \"activity_level\": \"moderate\",
        \"medical_conditions\": [\"hypertension\"],
        \"medications\": [\"lisinopril\"],
        \"dietary_restrictions\": [\"gluten_free\"],
        \"persona\": \"coach\",
        \"language\": \"en\",
        \"timezone\": \"America/New_York\"
    }")
check_status "Onboard new user" "201" "$ONBOARD_RESP"
ONBOARD_BODY=$(body_of "$ONBOARD_RESP")
check_truthy "user_id returned" ".user_id" "$ONBOARD_BODY"
check_field  "persona = coach"  ".persona" "coach" "$ONBOARD_BODY"

TEST_USER_ID=$(printf '%s' "$ONBOARD_BODY" | jq -r ".user_id")
if [ -z "$TEST_USER_ID" ] || [ "$TEST_USER_ID" = "null" ]; then
    printf "${RED}Cannot extract TEST_USER_ID — aborting.${NC}\n"; exit 1
fi
printf "  → TEST_USER_ID = %s\n" "$TEST_USER_ID"

# ─── 2. GET /users/by-email ────────────────────────────────────────
section "2. GET /users/by-email — has_profile after onboard"

ENCODED="${TEST_EMAIL/@/%40}"
BY_EMAIL_RESP=$(vcurl "$BASE/users/by-email/$ENCODED")
check_status "GET by-email for new user" "200" "$BY_EMAIL_RESP"
BY_EMAIL_BODY=$(body_of "$BY_EMAIL_RESP")
check_field "has_profile = true"  ".has_profile" "true"       "$BY_EMAIL_BODY"
check_field "email matches"       ".email"        "$TEST_EMAIL" "$BY_EMAIL_BODY"
check_field "persona = coach"     ".persona"      "coach"       "$BY_EMAIL_BODY"

# Unknown email → 404
NOTFOUND_RESP=$(vcurl "$BASE/users/by-email/nobody%40nowhere.com")
check_status "by-email unknown → 404" "404" "$NOTFOUND_RESP"

# User with no health profile → has_profile = false (local test data only)
NO_PROF_BY_EMAIL_RESP=$(vcurl "$BASE/users/by-email/test2%40test.com")
NO_PROF_BY_EMAIL_STATUS=$(status_of "$NO_PROF_BY_EMAIL_RESP")
if [ "$NO_PROF_BY_EMAIL_STATUS" = "200" ]; then
    check_field "test2@test.com has_profile = false" ".has_profile" "false" "$(body_of "$NO_PROF_BY_EMAIL_RESP")"
else
    printf "  ⚠ SKIP test2@test.com has_profile check — user not seeded in this environment (HTTP $NO_PROF_BY_EMAIL_STATUS)\n"
fi

# ─── 3. GET /users/{user_id} ──────────────────────────────────────
section "3. GET /users/{user_id}"

GET_USER_RESP=$(vcurl "$BASE/users/$TEST_USER_ID")
check_status "GET /users/{user_id}" "200" "$GET_USER_RESP"
GET_USER_BODY=$(body_of "$GET_USER_RESP")
check_field  "full_name correct"  ".full_name" "E2E Test User" "$GET_USER_BODY"
check_field  "email correct"      ".email"     "$TEST_EMAIL"   "$GET_USER_BODY"
check_truthy "onboarded_at set"   ".onboarded_at"              "$GET_USER_BODY"

# Unknown user → 404
check_status "GET /users unknown → 404" "404" \
    "$(vcurl "$BASE/users/00000000-0000-0000-0000-000000000000")"

# ─── 4. DB: date_of_birth (Bug #1 regression) ─────────────────────
section "4. DB — date_of_birth + profile fields saved (Bug #1 regression)"

IS_LOCAL=$(printf '%s' "$BASE" | grep -c 'localhost')
if [ "$HAS_PSQL" = "1" ] && [ "$IS_LOCAL" = "1" ]; then
    DB_ROW=$(psql vitacompanion -t -A -F'|' -c \
        "SELECT u.date_of_birth::text, hp.starting_weight_kg::text, hp.primary_goal::text
         FROM users u JOIN user_health_profiles hp ON hp.user_id = u.id
         WHERE u.id = '$TEST_USER_ID'" 2>/dev/null)
    if [ -n "$DB_ROW" ]; then
        DB_DOB=$(printf '%s'  "$DB_ROW" | cut -d'|' -f1)
        DB_SW=$(printf '%s'   "$DB_ROW" | cut -d'|' -f2)
        DB_GOAL=$(printf '%s' "$DB_ROW" | cut -d'|' -f3)

        [ "$DB_DOB" = "1975-06-20" ] \
            && pass "date_of_birth saved: $DB_DOB" \
            || fail "date_of_birth saved" "expected 1975-06-20, got '$DB_DOB'"

        case "$DB_SW" in
            70|70.0) pass "starting_weight_kg saved: $DB_SW" ;;
            *) fail "starting_weight_kg saved" "expected 70, got '$DB_SW'" ;;
        esac

        [ "$DB_GOAL" = "weight_loss" ] \
            && pass "primary_goal saved: $DB_GOAL" \
            || fail "primary_goal saved" "expected weight_loss, got '$DB_GOAL'"
    else
        fail "DB check (test user)" "no health_profile row found — JOIN returned nothing"
    fi

    # sharon.magen@gmail.com regression check
    SHARON_ROW=$(psql vitacompanion -t -A -F'|' -c \
        "SELECT u.date_of_birth::text, hp.primary_goal::text, hp.starting_weight_kg::text
         FROM users u JOIN user_health_profiles hp ON hp.user_id = u.id
         WHERE u.email = 'sharon.magen@gmail.com'" 2>/dev/null)
    if [ -n "$SHARON_ROW" ]; then
        S_DOB=$(printf '%s'    "$SHARON_ROW" | cut -d'|' -f1)
        S_GOAL=$(printf '%s'   "$SHARON_ROW" | cut -d'|' -f2)
        S_SW=$(printf '%s'     "$SHARON_ROW" | cut -d'|' -f3)
        [ -n "$S_DOB" ]  && pass "sharon: date_of_birth set ($S_DOB)"  || fail "sharon: date_of_birth" "NULL"
        [ -n "$S_GOAL" ] && pass "sharon: primary_goal set ($S_GOAL)"  || fail "sharon: primary_goal" "NULL"
        [ -n "$S_SW" ]   && pass "sharon: starting_weight_kg set ($S_SW)" || fail "sharon: starting_weight_kg" "NULL"
    else
        fail "sharon.magen@gmail.com" "no health_profile row in DB"
    fi
else
    if [ "$IS_LOCAL" = "0" ]; then
        printf "  ⚠ Skipping local DB checks (running against non-local BASE: $BASE)\n"
    else
        printf "  ⚠ Skipping DB checks (psql not available)\n"
    fi
fi

# ─── 5. POST /logs/daily ──────────────────────────────────────────
section "5. POST /logs/daily"

DAILY_RESP=$(vcurl -X POST "$BASE/logs/daily" \
    -H "Content-Type: application/json" \
    -d "{
        \"user_id\": \"$TEST_USER_ID\",
        \"log_date\": \"$TODAY\",
        \"weight_kg\": 69.8,
        \"energy_level\": 4,
        \"mood_score\": 4,
        \"sleep_hours\": 7.5,
        \"notes\": \"E2E test run\"
    }")
check_status "POST /logs/daily" "201" "$DAILY_RESP"
check_field  "log_date correct" ".log_date" "$TODAY" "$(body_of "$DAILY_RESP")"

# Upsert same day — should succeed (not duplicate)
UPSERT_RESP=$(vcurl -X POST "$BASE/logs/daily" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":\"$TEST_USER_ID\",\"log_date\":\"$TODAY\",\"mood_score\":5}")
check_status "POST /logs/daily upsert (same day)" "201" "$UPSERT_RESP"

# Pain flag
PAIN_RESP=$(vcurl -X POST "$BASE/logs/daily" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":\"$TEST_USER_ID\",\"log_date\":\"$TODAY\",\"pain_reported\":true,\"pain_detail\":\"knee\"}")
check_status "POST /logs/daily with pain_reported" "201" "$PAIN_RESP"

# ─── 6. POST /logs/meal — macro accumulation ──────────────────────
section "6. POST /logs/meal — macro accumulation"

MEAL1_RESP=$(vcurl -X POST "$BASE/logs/meal" \
    -H "Content-Type: application/json" \
    -d "{
        \"user_id\": \"$TEST_USER_ID\",
        \"log_date\": \"$TODAY\",
        \"meal_type\": \"breakfast\",
        \"description\": \"Oatmeal with berries\",
        \"calories\": 350,
        \"protein_g\": 12.0,
        \"fat_g\": 6.0,
        \"carbs_g\": 65.0
    }")
check_status "POST /logs/meal (breakfast)" "201" "$MEAL1_RESP"
check_field  "meal_type = breakfast" ".meal_type" "breakfast" "$(body_of "$MEAL1_RESP")"

MEAL2_RESP=$(vcurl -X POST "$BASE/logs/meal" \
    -H "Content-Type: application/json" \
    -d "{
        \"user_id\": \"$TEST_USER_ID\",
        \"log_date\": \"$TODAY\",
        \"meal_type\": \"lunch\",
        \"description\": \"Grilled chicken salad\",
        \"calories\": 480,
        \"protein_g\": 45.0,
        \"fat_g\": 14.0,
        \"carbs_g\": 28.0
    }")
check_status "POST /logs/meal (lunch)" "201" "$MEAL2_RESP"

# ─── 7. POST /logs/workout ────────────────────────────────────────
section "7. POST /logs/workout"

WORKOUT_RESP=$(vcurl -X POST "$BASE/logs/workout" \
    -H "Content-Type: application/json" \
    -d "{
        \"user_id\": \"$TEST_USER_ID\",
        \"log_date\": \"$TODAY\",
        \"session_type\": \"strength\",
        \"actual_duration_min\": 45,
        \"intensity\": \"moderate\",
        \"perceived_exertion\": 7,
        \"notes\": \"E2E test workout\"
    }")
check_status "POST /logs/workout" "201" "$WORKOUT_RESP"
check_field  "session_type = strength" ".session_type" "strength" "$(body_of "$WORKOUT_RESP")"

# ─── 8. GET /logs/daily — verify accumulated state ────────────────
section "8. GET /logs/daily — verify macro accumulation + workout flag"

GET_LOG_RESP=$(vcurl "$BASE/logs/daily/$TEST_USER_ID/$TODAY")
check_status "GET /logs/daily after all logs" "200" "$GET_LOG_RESP"
GET_LOG_BODY=$(body_of "$GET_LOG_RESP")

check_field "workout_completed = true" ".workout_completed" "true" "$GET_LOG_BODY"
check_field "pain_reported = true"     ".pain_reported"     "true" "$GET_LOG_BODY"
check_field "safety_flag_raised = true" ".safety_flag_raised" "true" "$GET_LOG_BODY"

CALS=$(printf '%s' "$GET_LOG_BODY" | jq -r ".calories_total")
if [ "$CALS" = "830" ]; then
    pass "Macro accumulation: calories_total = 830 (350 + 480)"
else
    fail "Macro accumulation" "expected 830, got $CALS"
fi

# No log for old date → 404
check_status "GET /logs/daily nonexistent date → 404" "404" \
    "$(vcurl "$BASE/logs/daily/$TEST_USER_ID/2020-01-01")"

# ─── 9. POST /chat — SSE streaming ───────────────────────────────
section "9. POST /chat — SSE streaming"

CHAT_OUT=$(curl -s -N --max-time 20 -X POST "$BASE/chat" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":\"$TEST_USER_ID\",\"message\":\"How many calories should I eat today?\"}" 2>&1)

printf '%s' "$CHAT_OUT" | grep -q '"chunk"' \
    && pass "Chat SSE: text chunks received" \
    || fail "Chat SSE: text chunks received" "no chunk data in stream"

printf '%s' "$CHAT_OUT" | grep -q '"done"' \
    && pass "Chat SSE: done event received" \
    || fail "Chat SSE: done event received" "no done event"

printf '%s' "$CHAT_OUT" | grep -q '"conversation_id"' \
    && pass "Chat SSE: conversation_id returned" \
    || fail "Chat SSE: conversation_id returned" "no conversation_id in done event"

# ─── 10. POST /scheduler/checkin ─────────────────────────────────
section "10. POST /scheduler/checkin"

CHECKIN_RESP=$(vcurl -X POST "$BASE/scheduler/checkin/$TEST_USER_ID" --max-time 30)
check_status "POST /scheduler/checkin" "200" "$CHECKIN_RESP"
check_truthy "checkin: message generated" ".message" "$(body_of "$CHECKIN_RESP")"

# ─── 11. POST /scheduler/nudge ───────────────────────────────────
section "11. POST /scheduler/nudge"

NUDGE_RESP=$(vcurl -X POST "$BASE/scheduler/nudge/$TEST_USER_ID" --max-time 30)
check_status "POST /scheduler/nudge" "200" "$NUDGE_RESP"
check_truthy "nudge: message generated" ".message" "$(body_of "$NUDGE_RESP")"

# ─── 12. GET /reports/weekly ─────────────────────────────────────
section "12. GET /reports/weekly"

WEEKLY_RESP=$(vcurl "$BASE/reports/weekly/$TEST_USER_ID" --max-time 30)
check_status "GET /reports/weekly" "200" "$WEEKLY_RESP"
check_truthy "weekly: narrative present" ".narrative" "$(body_of "$WEEKLY_RESP")"

# ─── 13. GET /reports/monthly ────────────────────────────────────
section "13. GET /reports/monthly"

MONTHLY_RESP=$(vcurl "$BASE/reports/monthly/$TEST_USER_ID" --max-time 30)
check_status "GET /reports/monthly" "200" "$MONTHLY_RESP"
check_truthy "monthly: narrative present" ".narrative" "$(body_of "$MONTHLY_RESP")"

# ─── 14. POST /users/{user_id}/persona/switch ────────────────────
section "14. POST /persona/switch"

SWITCH_RESP=$(vcurl -X POST "$BASE/users/$TEST_USER_ID/persona/switch" \
    -H "Content-Type: application/json" \
    -d '{"persona":"commander","reason":"E2E test"}')
check_status "switch to commander" "200" "$SWITCH_RESP"
SWITCH_BODY=$(body_of "$SWITCH_RESP")
check_field "active_persona = commander" ".active_persona"   "commander" "$SWITCH_BODY"
check_field "previous_persona = coach"   ".previous_persona" "coach"     "$SWITCH_BODY"

# Verify by-email reflects the switch
AFTER_SWITCH=$(vcurl "$BASE/users/by-email/$ENCODED")
check_field "by-email persona = commander after switch" ".persona" "commander" "$(body_of "$AFTER_SWITCH")"

# Switch back
vcurl -X POST "$BASE/users/$TEST_USER_ID/persona/switch" \
    -H "Content-Type: application/json" -d '{"persona":"friend"}' > /dev/null

# ─── 15. Onboard idempotency ──────────────────────────────────────
section "15. POST /users/onboard — idempotency (existing user)"

IDEM_RESP=$(vcurl -X POST "$BASE/users/onboard" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"$TEST_EMAIL\",
        \"full_name\": \"E2E Test User\",
        \"sso_provider\": \"google\",
        \"sso_id\": \"$TEST_SSO\",
        \"date_of_birth\": \"1975-06-20\",
        \"sex\": \"female\",
        \"height_cm\": 168.0,
        \"starting_weight_kg\": 70.0,
        \"primary_goal\": \"weight_loss\",
        \"activity_level\": \"moderate\",
        \"persona\": \"friend\",
        \"language\": \"en\",
        \"timezone\": \"America/New_York\"
    }")
check_status "Onboard existing user → 201" "201" "$IDEM_RESP"
IDEM_USER_ID=$(printf '%s' "$(body_of "$IDEM_RESP")" | jq -r ".user_id")
[ "$IDEM_USER_ID" = "$TEST_USER_ID" ] \
    && pass "Idempotency: same user_id returned" \
    || fail "Idempotency: same user_id returned" "expected $TEST_USER_ID, got $IDEM_USER_ID"

IDEM_CHECK=$(vcurl "$BASE/users/by-email/$ENCODED")
check_field "Idempotency: has_profile still true" ".has_profile" "true" "$(body_of "$IDEM_CHECK")"

# ─── 16. Edge cases — validation ─────────────────────────────────
section "16. Edge cases — input validation"

# Empty / whitespace chat message → 422
check_status "Empty chat message → 422" "422" \
    "$(vcurl -X POST "$BASE/chat" -H "Content-Type: application/json" \
        -d "{\"user_id\":\"$TEST_USER_ID\",\"message\":\"   \"}")"

# Negative calories → 422
check_status "Negative calories → 422" "422" \
    "$(vcurl -X POST "$BASE/logs/meal" -H "Content-Type: application/json" \
        -d "{\"user_id\":\"$TEST_USER_ID\",\"log_date\":\"$TODAY\",\"meal_type\":\"snack\",\"description\":\"x\",\"calories\":-100}")"

# Negative protein → 422
check_status "Negative protein_g → 422" "422" \
    "$(vcurl -X POST "$BASE/logs/meal" -H "Content-Type: application/json" \
        -d "{\"user_id\":\"$TEST_USER_ID\",\"log_date\":\"$TODAY\",\"meal_type\":\"snack\",\"description\":\"x\",\"protein_g\":-5}")"

# Negative weight_kg → 422
check_status "Negative weight_kg → 422" "422" \
    "$(vcurl -X POST "$BASE/logs/daily" -H "Content-Type: application/json" \
        -d "{\"user_id\":\"$TEST_USER_ID\",\"log_date\":\"$TODAY\",\"weight_kg\":-5}")"

# sleep_hours > 24 → 422
SLEEP25_RESP=$(vcurl -X POST "$BASE/logs/daily" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":\"$TEST_USER_ID\",\"log_date\":\"$TODAY\",\"sleep_hours\":25}")
check_status "sleep_hours=25 → 422" "422" "$SLEEP25_RESP"

# sleep_hours = 24 → valid boundary → 201
SLEEP24_RESP=$(vcurl -X POST "$BASE/logs/daily" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":\"$TEST_USER_ID\",\"log_date\":\"$TODAY\",\"sleep_hours\":24}")
check_status "sleep_hours=24 → 201 (valid boundary)" "201" "$SLEEP24_RESP"

# perceived_exertion = 0 → 422
EXERT0_RESP=$(vcurl -X POST "$BASE/logs/workout" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":\"$TEST_USER_ID\",\"log_date\":\"$TODAY\",\"session_type\":\"cardio\",\"perceived_exertion\":0}")
check_status "perceived_exertion=0 → 422" "422" "$EXERT0_RESP"

# perceived_exertion = 10 → valid boundary → 201
EXERT10_RESP=$(vcurl -X POST "$BASE/logs/workout" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":\"$TEST_USER_ID\",\"log_date\":\"$TODAY\",\"session_type\":\"cardio\",\"perceived_exertion\":10}")
check_status "perceived_exertion=10 → 201 (valid boundary)" "201" "$EXERT10_RESP"

# Invalid persona → 422
check_status "Invalid persona → 422" "422" \
    "$(vcurl -X POST "$BASE/users/$TEST_USER_ID/persona/switch" -H "Content-Type: application/json" \
        -d '{"persona":"drill_sergeant"}')"

# Chat for user with no health profile → should error (4xx or 5xx, not 200)
NO_PROF_CHAT=$(vcurl -X POST "$BASE/chat" -H "Content-Type: application/json" \
    -d "{\"user_id\":\"$NO_PROFILE_USER_ID\",\"message\":\"Hello\"}" --max-time 10)
NO_PROF_STATUS=$(status_of "$NO_PROF_CHAT")
if [ "$NO_PROF_STATUS" = "404" ] || [ "$NO_PROF_STATUS" = "422" ] || [ "$NO_PROF_STATUS" = "500" ]; then
    pass "Chat with no-profile user → HTTP $NO_PROF_STATUS (error correctly returned)"
else
    fail "Chat with no-profile user" "expected 4xx/5xx, got HTTP $NO_PROF_STATUS"
fi

# ─── 17. Age calculation regression (Bug #2) ──────────────────────
section "17. Age calculation regression (Bug #2)"

if [ "$HAS_PSQL" = "1" ]; then
    # Verify age is calculable (DOB exists, non-NULL)
    AGE_ROW=$(psql vitacompanion -t -A -c \
        "SELECT date_of_birth::text FROM users WHERE email = 'sharon.magen@gmail.com'" 2>/dev/null | tr -d ' ')
    if [ -n "$AGE_ROW" ] && [ "$AGE_ROW" != "" ]; then
        pass "sharon: date_of_birth is non-NULL ($AGE_ROW) — age calculation won't crash"
    else
        fail "sharon: date_of_birth" "NULL — age calculation in chat_service will error"
    fi

    # PostgreSQL age calculation for reference
    PG_AGE=$(psql vitacompanion -t -A -c \
        "SELECT EXTRACT(YEAR FROM AGE(date_of_birth))::int FROM users WHERE email = 'sharon.magen@gmail.com'" \
        2>/dev/null | tr -d ' ')
    if [ -n "$PG_AGE" ]; then
        pass "Age from DOB = ${PG_AGE}yo (PostgreSQL AGE() confirms calculation)"
    else
        fail "Age calculation" "could not compute age from DOB"
    fi

    # Verify the formula: (today - DOB).days // 365 equals PG_AGE
    # Fetch actual DOB from DB so the formula test is always correct
    SHARON_DOB=$(psql vitacompanion -t -A -c \
        "SELECT date_of_birth::text FROM users WHERE email = 'sharon.magen@gmail.com'" 2>/dev/null | tr -d ' ')
    PY_AGE=$(python3 -c "
from datetime import date
parts = '$SHARON_DOB'.split('-')
dob = date(int(parts[0]), int(parts[1]), int(parts[2]))
today = date(2026, 3, 18)
age = (today - dob).days // 365
print(age)
" 2>/dev/null)
    if [ "$PY_AGE" = "$PG_AGE" ]; then
        pass "Python age formula matches PostgreSQL AGE(): both = ${PY_AGE}yo"
    else
        fail "Age formula cross-check" "Python gives $PY_AGE, Postgres gives $PG_AGE"
    fi
else
    printf "  ⚠ Skipping DB age check (psql not available)\n"
fi

# ─── Summary ──────────────────────────────────────────────────────
printf "\n${BOLD}══════════════════════════════════════════${NC}\n"
printf "${BOLD}  Results: ${GREEN}${PASS} passed${NC}  ${RED}${FAIL} failed${NC}\n"
printf "${BOLD}══════════════════════════════════════════${NC}\n"
[ "$FAIL" -gt 0 ] && exit 1 || exit 0
