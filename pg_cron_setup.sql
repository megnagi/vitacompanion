-- ============================================================
-- VitaCompanion — pg_cron Setup
-- Run as a superuser connected to the vitacompanion database.
-- Requires PostgreSQL 12+ with pg_cron installed on the server.
-- ============================================================

-- 1. Enable extensions
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pg_net;  -- for HTTP calls; install from https://github.com/supabase/pg_net

-- Grant usage to the app DB user (replace 'vitauser' with your actual user)
GRANT USAGE ON SCHEMA cron TO vitauser;

-- ============================================================
-- Option A: Direct HTTP calls via pg_net
-- Calls POST /scheduler/checkin for every active user at 8:00 AM UTC.
-- Calls POST /scheduler/nudge for every active user at 6:00 PM UTC.
-- Replace 'http://localhost:8000' with your deployed backend URL.
-- ============================================================

SELECT cron.schedule(
    'vita-daily-checkin',
    '0 8 * * *',
    $$
        SELECT net.http_post(
            url    := 'http://localhost:8000/scheduler/checkin/' || id::text,
            body   := '{}'::jsonb,
            headers := '{"Content-Type": "application/json"}'::jsonb
        )
        FROM users
        WHERE is_active = TRUE;
    $$
);

SELECT cron.schedule(
    'vita-daily-nudge',
    '0 18 * * *',
    $$
        SELECT net.http_post(
            url    := 'http://localhost:8000/scheduler/nudge/' || id::text,
            body   := '{}'::jsonb,
            headers := '{"Content-Type": "application/json"}'::jsonb
        )
        FROM users
        WHERE is_active = TRUE;
    $$
);

-- ============================================================
-- Option B: Queue-based (if pg_net is unavailable)
-- pg_cron writes rows into a nudge_queue table.
-- scheduler_worker.py polls the table every minute and fires the API calls.
-- ============================================================

CREATE TABLE IF NOT EXISTS nudge_queue (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    nudge_type  TEXT NOT NULL CHECK (nudge_type IN ('checkin', 'nudge')),
    queued_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_nudge_queue_pending
    ON nudge_queue(queued_at) WHERE processed_at IS NULL;

-- Enqueue checkins at 8:00 AM UTC
SELECT cron.schedule(
    'vita-queue-checkin',
    '0 8 * * *',
    $$
        INSERT INTO nudge_queue (user_id, nudge_type)
        SELECT id, 'checkin'
        FROM users
        WHERE is_active = TRUE;
    $$
);

-- Enqueue nudges at 6:00 PM UTC
SELECT cron.schedule(
    'vita-queue-nudge',
    '0 18 * * *',
    $$
        INSERT INTO nudge_queue (user_id, nudge_type)
        SELECT id, 'nudge'
        FROM users
        WHERE is_active = TRUE;
    $$
);

-- ============================================================
-- Inspect / manage jobs
-- ============================================================

-- List scheduled jobs:
-- SELECT * FROM cron.job;

-- Unschedule a job:
-- SELECT cron.unschedule('vita-daily-checkin');
-- SELECT cron.unschedule('vita-daily-nudge');
-- SELECT cron.unschedule('vita-queue-checkin');
-- SELECT cron.unschedule('vita-queue-nudge');

-- View execution history:
-- SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 20;
