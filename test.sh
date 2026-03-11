#!/bin/bash

USER_ID="9f6e1f8c-bf14-4e26-9497-836704795ab2"  # from your earlier test
TODAY="2026-03-07"

echo "--- Daily Log ---"
curl -s -X POST http://127.0.0.1:8000/logs/daily \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"log_date\": \"$TODAY\",
    \"weight_kg\": 71.5,
    \"energy_level\": 4,
    \"mood_score\": 3,
    \"sleep_hours\": 7.5,
    \"water_ml\": 1500
  }" | python3 -m json.tool

echo "--- Meal Log ---"
curl -s -X POST http://127.0.0.1:8000/logs/meal \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"log_date\": \"$TODAY\",
    \"meal_type\": \"breakfast\",
    \"description\": \"2 eggs, whole wheat toast, coffee\",
    \"calories\": 380,
    \"protein_g\": 22,
    \"fat_g\": 14,
    \"carbs_g\": 35,
    \"on_plan\": true
  }" | python3 -m json.tool

echo "--- Workout Log ---"
curl -s -X POST http://127.0.0.1:8000/logs/workout \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"log_date\": \"$TODAY\",
    \"session_type\": \"strength\",
    \"actual_duration_min\": 45,
    \"intensity\": \"moderate\",
    \"perceived_exertion\": 6,
    \"pain_during\": false
  }" | python3 -m json.tool

chat_sse() {
  local message="$1"
  local label="$2"
  echo "--- Chat: $label ---"
  curl -s -N -X POST http://127.0.0.1:8000/chat \
    -H "Content-Type: application/json" \
    -d "{\"user_id\": \"$USER_ID\", \"message\": \"$message\"}" \
  | while IFS= read -r line; do
      echo "$line"
    done
  echo ""
}

chat_sse "Hey, how did I do today?" "first Claude call"
chat_sse "How much protein should I be eating at my age? I had 22g at breakfast — is that enough?" "nutrition RAG"
chat_sse "I finished my strength workout but my heart rate hit 155 bpm. Is that safe for me?" "training RAG"

echo "--- Scheduler Check-in ---"
curl -s -X POST http://127.0.0.1:8000/scheduler/checkin/$USER_ID \
  | python3 -m json.tool

echo "--- Scheduler Nudge ---"
curl -s -X POST http://127.0.0.1:8000/scheduler/nudge/$USER_ID \
  | python3 -m json.tool

echo "--- Weekly Report ---"
curl -s http://127.0.0.1:8000/reports/weekly/$USER_ID \
  | python3 -m json.tool

echo "--- Monthly Report ---"
curl -s http://127.0.0.1:8000/reports/monthly/$USER_ID \
  | python3 -m json.tool
