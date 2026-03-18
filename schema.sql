-- ============================================================
-- VitaCompanion — Full Database Schema
-- PostgreSQL 15+ with pgvector
-- Run this once on a fresh DB
-- ============================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
--CREATE EXTENSION IF NOT EXISTS pg_cron;  -- scheduler (run as superuser)

-- ============================================================
-- ENUM TYPES
-- ============================================================

CREATE TYPE persona_style   AS ENUM ('friend', 'coach', 'commander');
CREATE TYPE goal_type       AS ENUM ('weight_loss', 'muscle_gain', 'maintenance', 'endurance', 'general_health');
CREATE TYPE sex_type        AS ENUM ('male', 'female', 'other');
CREATE TYPE activity_level  AS ENUM ('sedentary', 'light', 'moderate', 'active', 'very_active');
CREATE TYPE plan_status     AS ENUM ('active', 'archived', 'paused');
CREATE TYPE session_type    AS ENUM ('cardio', 'strength', 'mobility', 'rest', 'active_recovery');
CREATE TYPE intensity_level AS ENUM ('low', 'moderate', 'moderate_high', 'high');
CREATE TYPE flag_type       AS ENUM ('none', 'physical', 'emotional', 'constraint_violation', 'rapid_weight_loss', 'pain_reported', 'hr_exceeded', 'overtraining_risk', 'medical_hold');
CREATE TYPE message_role    AS ENUM ('user', 'assistant', 'system');
CREATE TYPE bot_type        AS ENUM ('orchestrator', 'nutrition', 'training', 'reporting', 'scheduler');
CREATE TYPE nudge_channel   AS ENUM ('whatsapp', 'sms', 'in_app');
CREATE TYPE nudge_status    AS ENUM ('pending', 'sent', 'delivered', 'failed');
CREATE TYPE report_period   AS ENUM ('weekly', 'monthly', 'on_demand');

-- ============================================================
-- USERS
-- Core identity + onboarding data
-- ============================================================

CREATE TABLE users (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number        TEXT UNIQUE,                    -- WhatsApp (nullable — SSO users may have none)
    full_name           TEXT NOT NULL,
    email               TEXT UNIQUE,
    date_of_birth       DATE NOT NULL,
    sex                 sex_type NOT NULL,
    height_cm           NUMERIC(5,1) NOT NULL,
    timezone            TEXT NOT NULL DEFAULT 'Asia/Jerusalem',
    language            TEXT NOT NULL DEFAULT 'he',    -- 'he' | 'en'
    onboarded_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    sso_provider        VARCHAR(50),                   -- 'google', 'apple', etc.
    sso_id              VARCHAR(255),                  -- provider-specific user ID
    avatar_url          TEXT                           -- profile picture URL from SSO
);

-- ============================================================
-- USER HEALTH PROFILE
-- Medical context, goals, dietary constraints
-- One row per user, updated in place (versioned via audit log)
-- ============================================================

CREATE TABLE user_health_profiles (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Goals
    primary_goal            goal_type NOT NULL,
    target_weight_kg        NUMERIC(5,1),
    activity_level          activity_level NOT NULL DEFAULT 'moderate',
    
    -- Starting point
    starting_weight_kg      NUMERIC(5,1) NOT NULL,
    
    -- Medical
    medical_conditions      TEXT[],                    -- ['type2_diabetes', 'hypertension', ...]
    medications             TEXT[],
    injuries                TEXT[],
    physician_clearance     BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Dietary
    dietary_restrictions    TEXT[],                    -- ['gluten_free', 'lactose_intolerant', ...]
    allergies               TEXT[],
    preferred_cuisines      TEXT[],
    
    -- Bloodwork (latest values stored flat — easier to query)
    blood_glucose_fasting   NUMERIC(6,2),              -- mg/dL
    hba1c                   NUMERIC(4,2),              -- %
    cholesterol_ldl         NUMERIC(6,2),
    cholesterol_hdl         NUMERIC(6,2),
    triglycerides           NUMERIC(6,2),
    blood_pressure_systolic INT,
    blood_pressure_diastolic INT,
    bloodwork_date          DATE,
    
    -- Coaching intelligence (updated by Orchestrator over time)
    past_barriers           TEXT[],
    motivators              TEXT[],
    emotional_triggers      TEXT[],
    
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(user_id)
);

-- ============================================================
-- PERSONA CONFIG
-- Per-user, switchable at any time
-- ============================================================

CREATE TABLE user_persona_configs (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    active_persona          persona_style NOT NULL DEFAULT 'friend',
    humor_tolerance         SMALLINT NOT NULL DEFAULT 5 CHECK (humor_tolerance BETWEEN 1 AND 10),
    praise_frequency        SMALLINT NOT NULL DEFAULT 5 CHECK (praise_frequency BETWEEN 1 AND 10),
    custom_tone_notes       TEXT,                      -- free-form overrides
    safety_override_active  BOOLEAN NOT NULL DEFAULT TRUE,  -- ALWAYS true
    switched_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(user_id)
);

-- Persona switch history (audit only)
CREATE TABLE persona_switch_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    from_persona    persona_style,
    to_persona      persona_style NOT NULL,
    reason          TEXT,
    switched_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- SCHEDULER STATE
-- One row per user — the scheduler reads/writes this
-- ============================================================

CREATE TABLE user_scheduler_state (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Check-ins
    preferred_checkin_time      TIME NOT NULL DEFAULT '08:00',
    next_checkin_at             TIMESTAMPTZ,
    last_checkin_at             TIMESTAMPTZ,
    
    -- Nudges
    last_nudge_sent_at          TIMESTAMPTZ,
    days_since_last_weigh_in    INT NOT NULL DEFAULT 0,
    nudge_paused_until          TIMESTAMPTZ,           -- safety flag can pause nudges
    quiet_hours_start           TIME DEFAULT '22:00',
    quiet_hours_end             TIME DEFAULT '07:00',
    max_nudges_per_day          SMALLINT NOT NULL DEFAULT 3,
    
    -- Reports
    next_weekly_report_at       TIMESTAMPTZ,
    next_monthly_report_at      TIMESTAMPTZ,
    
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(user_id)
);

-- ============================================================
-- DAILY LOGS
-- One row per user per day — the core data
-- ============================================================

CREATE TABLE daily_logs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    log_date            DATE NOT NULL,
    
    -- Weight
    weight_kg           NUMERIC(5,1),
    weight_logged_at    TIMESTAMPTZ,
    
    -- Nutrition (totals — detail in meal_logs)
    calories_total      INT,
    protein_g           NUMERIC(6,1),
    fat_g               NUMERIC(6,1),
    carbs_g             NUMERIC(6,1),
    water_ml            INT,
    
    -- Calorie targets (copied from plan at time of log for comparison)
    calorie_target      INT,
    protein_target_g    NUMERIC(6,1),
    
    -- Training
    workout_completed   BOOLEAN,
    workout_skipped     BOOLEAN DEFAULT FALSE,
    skip_reason         TEXT,
    
    -- Subjective
    energy_level        SMALLINT CHECK (energy_level BETWEEN 1 AND 5),
    mood_score          SMALLINT CHECK (mood_score BETWEEN 1 AND 5),
    sleep_hours         NUMERIC(3,1),
    pain_reported       BOOLEAN NOT NULL DEFAULT FALSE,
    pain_detail         TEXT,
    
    -- Flags
    safety_flag_raised  BOOLEAN NOT NULL DEFAULT FALSE,
    flag_type           flag_type DEFAULT 'none',
    flag_detail         TEXT,
    
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(user_id, log_date)
);

-- ============================================================
-- MEAL LOGS
-- Individual meals within a day
-- ============================================================

CREATE TABLE meal_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    daily_log_id    UUID NOT NULL REFERENCES daily_logs(id) ON DELETE CASCADE,
    log_date        DATE NOT NULL,
    meal_type       TEXT NOT NULL,                     -- 'breakfast' | 'lunch' | 'dinner' | 'snack'
    logged_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    description     TEXT NOT NULL,                     -- raw user input
    calories        INT,
    protein_g       NUMERIC(5,1),
    fat_g           NUMERIC(5,1),
    carbs_g         NUMERIC(5,1),
    
    on_plan         BOOLEAN,                           -- did this match the nutrition plan?
    notes           TEXT
);

-- ============================================================
-- WORKOUT LOGS
-- Detailed training session records
-- ============================================================

CREATE TABLE workout_logs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    daily_log_id        UUID NOT NULL REFERENCES daily_logs(id) ON DELETE CASCADE,
    log_date            DATE NOT NULL,
    
    session_type        session_type NOT NULL,
    planned_duration_min INT,
    actual_duration_min  INT,
    intensity           intensity_level,
    
    -- Cardio
    avg_hr_bpm          INT,
    max_hr_bpm          INT,
    hr_zone_target      TEXT,                          -- e.g. "95-115 bpm"
    hr_zone_exceeded    BOOLEAN DEFAULT FALSE,
    
    exercises           JSONB,                         -- [{name, sets, reps, weight_kg, notes}]
    
    perceived_exertion  SMALLINT CHECK (perceived_exertion BETWEEN 1 AND 10),
    pain_during         BOOLEAN DEFAULT FALSE,
    pain_detail         TEXT,
    
    notes               TEXT,
    logged_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- NUTRITION PLANS
-- Versioned — a new row on every plan update
-- ============================================================

CREATE TABLE nutrition_plans (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    version             SMALLINT NOT NULL DEFAULT 1,
    status              plan_status NOT NULL DEFAULT 'active',
    persona_at_creation persona_style NOT NULL,
    
    -- Targets
    daily_calories      INT NOT NULL,
    protein_g           NUMERIC(6,1) NOT NULL,
    fat_g               NUMERIC(6,1) NOT NULL,
    carbs_g             NUMERIC(6,1) NOT NULL,
    
    -- Plan detail
    meal_structure      JSONB NOT NULL,                -- {breakfast, lunch, dinner, snacks[]}
    foods_to_emphasize  TEXT[],
    foods_to_avoid      TEXT[],
    
    bot_rationale       TEXT,                          -- clinical justification
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_at         TIMESTAMPTZ
);

-- ============================================================
-- TRAINING PLANS
-- Versioned — same pattern as nutrition plans
-- ============================================================

CREATE TABLE training_plans (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    version             SMALLINT NOT NULL DEFAULT 1,
    status              plan_status NOT NULL DEFAULT 'active',
    persona_at_creation persona_style NOT NULL,
    
    sessions_per_week   SMALLINT NOT NULL,
    weekly_structure    JSONB NOT NULL,                -- [{day, session_type, duration_min, intensity, exercises[]}]
    
    -- Constraints applied
    excluded_exercises  TEXT[],
    injury_modifications TEXT[],
    
    bot_rationale       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_at         TIMESTAMPTZ
);

-- ============================================================
-- CONVERSATIONS
-- Full message history per user
-- ============================================================

CREATE TABLE conversations (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    started_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at    TIMESTAMPTZ,
    channel     nudge_channel NOT NULL DEFAULT 'whatsapp',
    metadata    JSONB                                  -- session context, trigger source, etc.
);

CREATE TABLE messages (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id     UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role                message_role NOT NULL,
    bot_source          bot_type,                      -- which bot generated this (null for user messages)
    
    content             TEXT NOT NULL,                 -- human-readable content
    raw_bot_response    JSONB,                         -- full structured JSON response from bot
    persona_applied     persona_style,
    
    safety_flag_raised  BOOLEAN NOT NULL DEFAULT FALSE,
    flag_type           flag_type DEFAULT 'none',
    
    token_count         INT,                           -- for cost tracking
    latency_ms          INT,                           -- API response time
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- RAG / VECTOR MEMORY
-- Embeddings for semantic retrieval
-- ============================================================

CREATE TABLE rag_documents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,        -- NULL = global doc
    
    doc_type        TEXT NOT NULL,                     -- 'profile' | 'daily_log' | 'plan' | 'conversation' | 'coaching_insight'
    source_id       UUID,                              -- FK to the source row (daily_log, message, etc.)
    content         TEXT NOT NULL,                     -- the text that was embedded
    embedding       vector(1536),                      -- OpenAI ada-002 dims (use 1024 for claude embeddings)
    
    metadata        JSONB,                             -- {date, tags, importance_score, ...}
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ                        -- null = keep forever
);

-- ============================================================
-- NUDGE LOG
-- Every outbound notification sent
-- ============================================================

CREATE TABLE nudge_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel         nudge_channel NOT NULL DEFAULT 'whatsapp',
    
    nudge_type      TEXT NOT NULL,                     -- 'checkin_reminder' | 'weigh_in_reminder' | 'motivational' | 'safety' | 'report_ready'
    content         TEXT NOT NULL,
    status          nudge_status NOT NULL DEFAULT 'pending',
    
    scheduled_at    TIMESTAMPTZ NOT NULL,
    sent_at         TIMESTAMPTZ,
    delivered_at    TIMESTAMPTZ,
    error_detail    TEXT,
    
    twilio_sid      TEXT                               -- Twilio message SID for tracking
);

-- ============================================================
-- WEEKLY / MONTHLY REPORTS
-- Snapshot stored after each report generation
-- ============================================================

CREATE TABLE reports (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    period              report_period NOT NULL,
    period_start        DATE NOT NULL,
    period_end          DATE NOT NULL,
    
    -- Computed metrics (denormalized for fast retrieval)
    avg_daily_calories  INT,
    calorie_adherence_pct NUMERIC(5,2),
    avg_protein_g       NUMERIC(6,1),
    weight_start_kg     NUMERIC(5,1),
    weight_end_kg       NUMERIC(5,1),
    weight_delta_kg     NUMERIC(5,1),
    workouts_completed  SMALLINT,
    workouts_planned    SMALLINT,
    workout_adherence_pct NUMERIC(5,2),
    avg_energy          NUMERIC(3,1),
    avg_mood            NUMERIC(3,1),
    avg_sleep_hours     NUMERIC(3,1),
    
    -- Flags
    anomalies_detected  JSONB,                         -- [{type, detail, date}]
    doctor_review_flag  BOOLEAN DEFAULT FALSE,
    
    -- Content
    narrative_summary   TEXT,                          -- persona-voiced narrative
    chart_data          JSONB,                         -- pre-computed chart datasets
    raw_report_json     JSONB,                         -- full structured report
    
    generated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    persona_at_generation persona_style NOT NULL
);

-- ============================================================
-- INDEXES
-- ============================================================

-- Users
CREATE INDEX idx_users_phone ON users(phone_number);

-- Daily logs — most-queried table
CREATE INDEX idx_daily_logs_user_date ON daily_logs(user_id, log_date DESC);
CREATE INDEX idx_daily_logs_date ON daily_logs(log_date);
CREATE INDEX idx_daily_logs_safety ON daily_logs(user_id) WHERE safety_flag_raised = TRUE;

-- Meal & workout logs
CREATE INDEX idx_meal_logs_user_date ON meal_logs(user_id, log_date DESC);
CREATE INDEX idx_workout_logs_user_date ON workout_logs(user_id, log_date DESC);

-- Messages
CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at DESC);
CREATE INDEX idx_messages_user ON messages(user_id, created_at DESC);
CREATE INDEX idx_messages_safety ON messages(user_id) WHERE safety_flag_raised = TRUE;

-- Plans (get active plan fast)
CREATE INDEX idx_nutrition_plans_active ON nutrition_plans(user_id) WHERE status = 'active';
CREATE INDEX idx_training_plans_active ON training_plans(user_id) WHERE status = 'active';

-- RAG vector search (IVFFlat — good for MVP scale)
CREATE INDEX idx_rag_embedding ON rag_documents 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);
CREATE INDEX idx_rag_user_type ON rag_documents(user_id, doc_type);

-- Nudge log
CREATE INDEX idx_nudge_log_user ON nudge_log(user_id, scheduled_at DESC);
CREATE INDEX idx_nudge_log_pending ON nudge_log(status, scheduled_at) WHERE status = 'pending';

-- Reports
CREATE INDEX idx_reports_user_period ON reports(user_id, period_start DESC);

-- Scheduler
CREATE INDEX idx_scheduler_next_checkin ON user_scheduler_state(next_checkin_at) 
    WHERE next_checkin_at IS NOT NULL;

-- ============================================================
-- AUTO-UPDATE updated_at TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_health_profiles_updated_at
    BEFORE UPDATE ON user_health_profiles
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_daily_logs_updated_at
    BEFORE UPDATE ON daily_logs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_scheduler_updated_at
    BEFORE UPDATE ON user_scheduler_state
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- pg_cron JOB STUBS
-- (Activate after tables exist — adjust times to your TZ)
-- ============================================================

-- Daily check-in trigger (runs every minute, Orchestrator filters by next_checkin_at)
-- SELECT cron.schedule('vita-checkin-trigger', '* * * * *', $$
--     UPDATE user_scheduler_state
--     SET last_checkin_at = NOW(),
--         next_checkin_at = NOW() + INTERVAL '1 day'
--     WHERE next_checkin_at <= NOW() AND nudge_paused_until IS NULL;
-- $$);

-- Weekly report trigger (every Sunday at 06:00 IL time)
-- SELECT cron.schedule('vita-weekly-report', '0 6 * * 0', $$
--     UPDATE user_scheduler_state
--     SET next_weekly_report_at = NOW() + INTERVAL '7 days'
--     WHERE next_weekly_report_at <= NOW();
-- $$);