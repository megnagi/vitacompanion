const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
  LevelFormat, PageBreak, VerticalAlign, ImageRun
} = require('docx');
const fs = require('fs');

const flowchartPng = fs.readFileSync('/home/claude/flowchart3.png');

const COLORS = {
  sage: '4A6B52',
  sageLight: 'A8C4B0',
  sagePale: 'E8F4EC',
  accent: 'C17B4E',
  accentPale: 'FDF0E8',
  teal: '5B9E98',
  tealPale: 'E8F8F4',
  rose: 'C4848A',
  rosePale: 'FAE8E9',
  lavender: '9B8EB8',
  lavPale: 'EDE9F8',
  amber: 'C9A227',
  amberPale: 'FFF8E8',
  sky: '7BA7BC',
  skyPale: 'E8F4FA',
  charcoal: '2C2C2C',
  muted: '7A7A7A',
  white: 'FFFFFF',
  cream: 'FAF7F2',
  green: '2E7D32',
  greenPale: 'E8F5E9',
  red: 'C62828',
  redPale: 'FFEBEE',
  gray: 'F5F5F5',
  borderGray: 'E0E0E0',
};

const border = (color = COLORS.borderGray) => ({
  top: { style: BorderStyle.SINGLE, size: 1, color },
  bottom: { style: BorderStyle.SINGLE, size: 1, color },
  left: { style: BorderStyle.SINGLE, size: 1, color },
  right: { style: BorderStyle.SINGLE, size: 1, color },
});

const noBorder = () => ({
  top: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' },
  bottom: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' },
  left: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' },
  right: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' },
});

const cellMargins = { top: 100, bottom: 100, left: 140, right: 140 };

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 160 },
    children: [new TextRun({ text, bold: true, size: 36, color: COLORS.sage, font: 'Arial' })],
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 120 },
    children: [new TextRun({ text, bold: true, size: 28, color: COLORS.charcoal, font: 'Arial' })],
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 80 },
    children: [new TextRun({ text, bold: true, size: 24, color: COLORS.sage, font: 'Arial' })],
  });
}

function para(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 60, after: 80 },
    children: [new TextRun({ text, size: 22, color: COLORS.charcoal, font: 'Arial', ...opts })],
  });
}

function spacer(pts = 120) {
  return new Paragraph({ spacing: { before: pts, after: 0 }, children: [new TextRun('')] });
}

function bullet(text, level = 0) {
  return new Paragraph({
    numbering: { reference: 'bullets', level },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text, size: 22, color: COLORS.charcoal, font: 'Arial' })],
  });
}

function statusBadge(label, color, bgColor) {
  return new TableCell({
    borders: noBorder(),
    shading: { fill: bgColor, type: ShadingType.CLEAR },
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    width: { size: 1400, type: WidthType.DXA },
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: label, bold: true, size: 18, color, font: 'Arial' })]
    })]
  });
}

function sectionDivider(title, color = COLORS.sage, bg = COLORS.sagePale) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [9360],
    rows: [new TableRow({ children: [
      new TableCell({
        borders: { top: { style: BorderStyle.SINGLE, size: 4, color }, bottom: { style: BorderStyle.SINGLE, size: 4, color }, left: { style: BorderStyle.SINGLE, size: 4, color }, right: { style: BorderStyle.SINGLE, size: 4, color } },
        shading: { fill: bg, type: ShadingType.CLEAR },
        margins: { top: 120, bottom: 120, left: 200, right: 200 },
        children: [new Paragraph({
          children: [new TextRun({ text: title, bold: true, size: 26, color, font: 'Arial' })]
        })]
      })
    ]})]
  });
}

function twoColTable(left, right, leftWidth = 4500, rightWidth = 4860) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [leftWidth, rightWidth],
    rows: [new TableRow({ children: [
      new TableCell({ borders: noBorder(), margins: { top: 0, bottom: 0, left: 0, right: 160 }, width: { size: leftWidth, type: WidthType.DXA }, children: left }),
      new TableCell({ borders: noBorder(), margins: { top: 0, bottom: 0, left: 160, right: 0 }, width: { size: rightWidth, type: WidthType.DXA }, children: right }),
    ]})]
  });
}

function statusTable(rows) {
  const headerRow = new TableRow({
    children: [
      new TableCell({ borders: border(COLORS.sage), shading: { fill: COLORS.sage, type: ShadingType.CLEAR }, margins: cellMargins, width: { size: 3500, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: 'Module / Endpoint', bold: true, size: 20, color: COLORS.white, font: 'Arial' })] })] }),
      new TableCell({ borders: border(COLORS.sage), shading: { fill: COLORS.sage, type: ShadingType.CLEAR }, margins: cellMargins, width: { size: 3760, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: 'Description', bold: true, size: 20, color: COLORS.white, font: 'Arial' })] })] }),
      new TableCell({ borders: border(COLORS.sage), shading: { fill: COLORS.sage, type: ShadingType.CLEAR }, margins: cellMargins, width: { size: 2100, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: 'Status', bold: true, size: 20, color: COLORS.white, font: 'Arial' })] })] }),
    ]
  });

  const dataRows = rows.map(([module, desc, status], i) => {
    const bg = i % 2 === 0 ? COLORS.white : COLORS.gray;
    const [statusText, statusColor, statusBg] = status === 'done'
      ? ['✅  BUILT', COLORS.green, COLORS.greenPale]
      : status === 'partial'
      ? ['🔧  PARTIAL', COLORS.amber, COLORS.amberPale]
      : ['⬜  TODO', COLORS.muted, COLORS.gray];

    return new TableRow({ children: [
      new TableCell({ borders: border(), shading: { fill: bg, type: ShadingType.CLEAR }, margins: cellMargins, width: { size: 3500, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: module, bold: true, size: 20, color: COLORS.charcoal, font: 'Arial' })] })] }),
      new TableCell({ borders: border(), shading: { fill: bg, type: ShadingType.CLEAR }, margins: cellMargins, width: { size: 3760, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: desc, size: 20, color: COLORS.charcoal, font: 'Arial' })] })] }),
      new TableCell({ borders: border(), shading: { fill: statusBg, type: ShadingType.CLEAR }, margins: cellMargins, width: { size: 2100, type: WidthType.DXA }, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: statusText, bold: true, size: 18, color: statusColor, font: 'Arial' })] })] }),
    ]});
  });

  return new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [3500, 3760, 2100], rows: [headerRow, ...dataRows] });
}

function infoBox(text, color, bg) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [9360],
    rows: [new TableRow({ children: [
      new TableCell({
        borders: { top: { style: BorderStyle.SINGLE, size: 6, color }, bottom: { style: BorderStyle.SINGLE, size: 6, color }, left: { style: BorderStyle.SINGLE, size: 6, color }, right: { style: BorderStyle.SINGLE, size: 6, color } },
        shading: { fill: bg, type: ShadingType.CLEAR },
        margins: { top: 120, bottom: 120, left: 200, right: 200 },
        children: [new Paragraph({ children: [new TextRun({ text, size: 20, color, font: 'Arial' })] })]
      })
    ]})]
  });
}

function stackTable(rows) {
  const headerRow = new TableRow({ children: [
    new TableCell({ borders: border(COLORS.teal), shading: { fill: COLORS.teal, type: ShadingType.CLEAR }, margins: cellMargins, width: { size: 2400, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: 'Layer', bold: true, size: 20, color: COLORS.white, font: 'Arial' })] })] }),
    new TableCell({ borders: border(COLORS.teal), shading: { fill: COLORS.teal, type: ShadingType.CLEAR }, margins: cellMargins, width: { size: 2880, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: 'Technology', bold: true, size: 20, color: COLORS.white, font: 'Arial' })] })] }),
    new TableCell({ borders: border(COLORS.teal), shading: { fill: COLORS.teal, type: ShadingType.CLEAR }, margins: cellMargins, width: { size: 4080, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: 'Role', bold: true, size: 20, color: COLORS.white, font: 'Arial' })] })] }),
  ]});

  const dataRows = rows.map(([layer, tech, role], i) => {
    const bg = i % 2 === 0 ? COLORS.white : COLORS.tealPale;
    return new TableRow({ children: [
      new TableCell({ borders: border(), shading: { fill: bg, type: ShadingType.CLEAR }, margins: cellMargins, width: { size: 2400, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: layer, bold: true, size: 20, color: COLORS.teal, font: 'Arial' })] })] }),
      new TableCell({ borders: border(), shading: { fill: bg, type: ShadingType.CLEAR }, margins: cellMargins, width: { size: 2880, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: tech, bold: true, size: 20, color: COLORS.charcoal, font: 'Arial' })] })] }),
      new TableCell({ borders: border(), shading: { fill: bg, type: ShadingType.CLEAR }, margins: cellMargins, width: { size: 4080, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: role, size: 20, color: COLORS.charcoal, font: 'Arial' })] })] }),
    ]});
  });

  return new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [2400, 2880, 4080], rows: [headerRow, ...dataRows] });
}

function dbTable(rows) {
  const headerRow = new TableRow({ children: [
    new TableCell({ borders: border(COLORS.lavender), shading: { fill: COLORS.lavender, type: ShadingType.CLEAR }, margins: cellMargins, width: { size: 2200, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: 'Table', bold: true, size: 20, color: COLORS.white, font: 'Arial' })] })] }),
    new TableCell({ borders: border(COLORS.lavender), shading: { fill: COLORS.lavender, type: ShadingType.CLEAR }, margins: cellMargins, width: { size: 4560, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: 'Purpose', bold: true, size: 20, color: COLORS.white, font: 'Arial' })] })] }),
    new TableCell({ borders: border(COLORS.lavender), shading: { fill: COLORS.lavender, type: ShadingType.CLEAR }, margins: cellMargins, width: { size: 2600, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: 'Key Fields', bold: true, size: 20, color: COLORS.white, font: 'Arial' })] })] }),
  ]});

  const dataRows = rows.map(([table, purpose, fields], i) => {
    const bg = i % 2 === 0 ? COLORS.white : COLORS.lavPale;
    return new TableRow({ children: [
      new TableCell({ borders: border(), shading: { fill: bg, type: ShadingType.CLEAR }, margins: cellMargins, width: { size: 2200, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: table, bold: true, size: 19, color: COLORS.lavender, font: 'Courier New' })] })] }),
      new TableCell({ borders: border(), shading: { fill: bg, type: ShadingType.CLEAR }, margins: cellMargins, width: { size: 4560, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: purpose, size: 20, color: COLORS.charcoal, font: 'Arial' })] })] }),
      new TableCell({ borders: border(), shading: { fill: bg, type: ShadingType.CLEAR }, margins: cellMargins, width: { size: 2600, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: fields, size: 18, color: COLORS.muted, font: 'Courier New' })] })] }),
    ]});
  });

  return new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [2200, 4560, 2600], rows: [headerRow, ...dataRows] });
}

// ─────────────────────────────────────────────
// DOCUMENT
// ─────────────────────────────────────────────

const doc = new Document({
  numbering: {
    config: [
      { reference: 'bullets', levels: [
        { level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 600, hanging: 300 } } } },
        { level: 1, format: LevelFormat.BULLET, text: '◦', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 960, hanging: 300 } } } },
      ]},
    ]
  },
  styles: {
    default: { document: { run: { font: 'Arial', size: 22 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 36, bold: true, font: 'Arial', color: COLORS.sage }, paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 28, bold: true, font: 'Arial', color: COLORS.charcoal }, paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 24, bold: true, font: 'Arial', color: COLORS.sage }, paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 2 } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children: [

      // ── COVER ──────────────────────────────────────────────
      spacer(480),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 60 },
        children: [new TextRun({ text: 'VitaCompanion', bold: true, size: 64, color: COLORS.sage, font: 'Arial' })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 60 },
        children: [new TextRun({ text: 'Product Requirements & Technical Architecture', size: 32, color: COLORS.muted, font: 'Arial' })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 40 },
        children: [new TextRun({ text: 'AI-Powered Wellness Coaching for 50+', size: 26, color: COLORS.accent, font: 'Arial', italics: true })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 60, after: 0 },
        children: [new TextRun({ text: `Version 1.0  ·  March 2026  ·  MVP Build`, size: 20, color: COLORS.muted, font: 'Arial' })]
      }),
      spacer(600),

      new Paragraph({ children: [new PageBreak()] }),

      // ── 1. PRODUCT OVERVIEW ────────────────────────────────
      h1('1. Product Overview'),
      para('VitaCompanion is an AI-powered health and wellness coaching platform designed specifically for users aged 50 and above. It combines structured data tracking (meals, workouts, weight, sleep, mood) with a conversational AI coaching layer powered by Claude, delivering personalised guidance through a chosen persona — the Warm Friend, the Structured Coach, or the Commander.'),
      spacer(),
      h2('1.1 Core Value Proposition'),
      bullet('Personalised coaching that adapts to individual health profiles, goals, and emotional needs'),
      bullet('Three distinct coaching personas selectable by the user, with a safety override layer always active'),
      bullet('Proactive nudges and check-ins delivered via WhatsApp or in-app notifications'),
      bullet('Weekly and monthly progress reports generated automatically'),
      bullet('Vector-powered memory (RAG) that gives every Claude call full awareness of user history'),
      spacer(),
      h2('1.2 Target User'),
      bullet('Age: 50+ (primary), 40+ (secondary)'),
      bullet('Goals: weight loss, muscle maintenance, general health, endurance'),
      bullet('Needs: accountability, simplicity, safety awareness, personalisation'),
      bullet('Access: web app (primary), WhatsApp nudges (secondary)'),
      spacer(),
      h2('1.3 Development Status'),
      infoBox('📍  Current Phase: Day 4 complete. Database, logging API, and first Claude integration are all working. POST /chat live, RAG retrieval working, Nutrition Bot and Training Bot routing confirmed. Intent detection routes correctly based on message content.', COLORS.sage, COLORS.sagePale),

      spacer(200),
      new Paragraph({ children: [new PageBreak()] }),

      // ── 2. TECH STACK ──────────────────────────────────────
      h1('2. Technology Stack'),
      spacer(80),
      stackTable([
        ['Frontend', 'Next.js / React', 'Web app, onboarding flow, dashboard, chat UI'],
        ['Backend API', 'Python + FastAPI', 'Async REST API, routing, business logic, Claude orchestration'],
        ['Database', 'PostgreSQL 16', 'Primary data store — 15-table schema'],
        ['Vector Search', 'pgvector 0.8.2', 'RAG embeddings (1536-dim, OpenAI ada-002), semantic search'],
        ['AI / LLM', 'Claude Sonnet (Anthropic)', 'Orchestrator, Nutrition Bot, Training Bot, Reporting Engine'],
        ['Embeddings', 'OpenAI text-embedding-ada-002', 'Document embedding for RAG memory store'],
        ['Scheduler', 'pg_cron', 'Database-level cron for nudges, check-ins, report generation'],
        ['Notifications', 'Twilio WhatsApp API', 'Proactive nudges, check-in reminders, weekly reports'],
        ['Auth', 'Google / Apple SSO', 'No password management — SSO only'],
        ['ORM', 'SQLAlchemy (async)', 'Database models, async session management'],
        ['Validation', 'Pydantic v2', 'Request/response schemas, type safety'],
        ['Hosting', 'TBD (post-MVP)', 'Local dev currently; cloud deployment after MVP validation'],
      ]),
      spacer(160),
      infoBox('🔧  Local Dev Stack: PostgreSQL via Homebrew (macOS), uvicorn --reload for hot-reload development, Python 3.13 virtual environment.', COLORS.teal, COLORS.tealPale),

      spacer(200),
      new Paragraph({ children: [new PageBreak()] }),

      // ── 3. DATABASE SCHEMA ─────────────────────────────────
      h1('3. Database Schema'),
      para('The PostgreSQL database contains 15 tables covering all aspects of user state, activity tracking, AI memory, scheduling, and reporting. All tables use UUID primary keys, TIMESTAMPTZ for all timestamps, and CASCADE deletes on user removal.'),
      spacer(80),

      h2('3.1 Core User Tables'),
      dbTable([
        ['users', 'Primary user record — SSO identity, demographics, timezone, language', 'sso_provider, sso_id, date_of_birth, sex, height_cm'],
        ['user_health_profiles', 'Health baseline — goals, activity level, medical data, bloodwork, dietary restrictions', 'primary_goal, activity_level, medical_conditions[], bloodwork fields'],
        ['user_persona_configs', 'Active coaching persona and tone settings', 'active_persona, humor_tolerance, praise_frequency, safety_override_active'],
        ['user_scheduler_state', 'Scheduler state — next check-in, nudge timing, quiet hours, report schedule', 'next_checkin_at, quiet_hours_start/end, max_nudges_per_day'],
      ]),
      spacer(120),

      h2('3.2 Activity & Logging Tables'),
      dbTable([
        ['daily_logs', 'Master daily entry — weight, nutrition totals, workout status, mood, sleep, safety flags', 'weight_kg, calories_total, energy_level, mood_score, flag_type'],
        ['meal_logs', 'Individual meal entries linked to daily_log — macros, meal type, on-plan flag', 'meal_type, description, calories, protein_g, on_plan'],
        ['workout_logs', 'Workout session details — type, duration, HR data, exercises (JSONB), pain flags', 'session_type, intensity, avg_hr_bpm, hr_zone_exceeded, pain_during'],
      ]),
      spacer(120),

      h2('3.3 AI & Planning Tables'),
      dbTable([
        ['conversations', 'Conversation sessions with bot_type tracking', 'bot_type, started_at, last_message_at, is_active'],
        ['messages', 'Individual messages with full raw bot response stored as JSONB', 'role, content, raw_bot_response, tokens_used'],
        ['rag_documents', 'Vector knowledge store — embeddings + metadata for semantic retrieval', 'embedding vector(1536), content, category, user_id'],
        ['nutrition_plans', 'Versioned nutrition plans — calorie/macro targets, meal structure', 'calorie_target, protein_target_g, status (active/archived)'],
        ['training_plans', 'Versioned workout plans — weekly schedule, approved exercise list', 'weekly_schedule JSONB, approved_exercises[], status'],
        ['persona_switch_log', 'Audit log of all persona changes with reasons', 'from_persona, to_persona, reason, switched_at'],
        ['nudge_log', 'Every nudge sent — channel, status, content, dedup logic', 'channel, status, content, sent_at'],
        ['reports', 'Weekly/monthly report snapshots — data payload + delivery status', 'period_type, report_data JSONB, generated_at'],
      ]),
      spacer(120),
      infoBox('📐  Vector Setup: pgvector extension active. IVFFlat index on rag_documents.embedding. 1536 dimensions compatible with OpenAI text-embedding-ada-002. Embeddings generated server-side before INSERT.', COLORS.lavender, COLORS.lavPale),

      spacer(200),
      new Paragraph({ children: [new PageBreak()] }),

      // ── 4. SYSTEM ARCHITECTURE ─────────────────────────────
      h1('4. System Architecture & Data Flow'),
      spacer(80),

      h2('4.1 High-Level Architecture'),
      para('VitaCompanion is organised into five functional layers that communicate through the FastAPI backend:'),
      spacer(60),
      bullet('User Layer — Next.js web app + Twilio WhatsApp for input and notifications'),
      bullet('API Layer — FastAPI handles all routing, validation, and orchestration calls'),
      bullet('AI Layer — Claude Orchestrator routes to specialist bots (Nutrition, Training, Reporting)'),
      bullet('Memory Layer — PostgreSQL + pgvector stores all structured data and semantic embeddings'),
      bullet('Scheduler Layer — pg_cron triggers proactive nudges and report generation'),

      spacer(120),
      h2('4.2 Conversation Data Flow'),
      infoBox('User message → FastAPI /chat → Load user context (profile + today\'s log + active plans + last 10 messages) → Semantic RAG search → Build Orchestrator system prompt → Claude API call → Parse response + route to specialist bot if needed → Save message to DB → Return response to user', COLORS.charcoal, COLORS.gray),
      spacer(120),

      h2('4.3 Orchestrator Routing Logic'),
      para('The Orchestrator (Claude) receives the full user context on every call and decides how to respond. It can:'),
      bullet('Respond directly in the user\'s chosen persona for general coaching, motivation, and check-ins'),
      bullet('Route to the Nutrition Bot when the user asks about meals, calories, macros, or food plans'),
      bullet('Route to the Training Bot for workout questions, session planning, or exercise modifications'),
      bullet('Route to the Reporting Engine to generate structured weekly or monthly reports'),
      bullet('Trigger a safety escalation if pain, emotional distress, or medical flags are detected — overriding the active persona regardless of user settings'),
      spacer(120),

      h2('4.4 Proactive Scheduler Flow'),
      para('pg_cron triggers scheduled jobs that call FastAPI endpoints:'),
      bullet('Daily check-in: fires at user\'s preferred_checkin_time, sends nudge if no log found for today'),
      bullet('Weigh-in reminder: fires if days_since_last_weigh_in > 3, sends gentle prompt'),
      bullet('Weekly report: fires every Sunday, triggers Reporting Engine, delivers via WhatsApp or in-app'),
      bullet('Monthly summary: fires on the 1st, generates trend analysis with bloodwork comparison'),
      bullet('Quiet hours: all nudges suppressed between quiet_hours_start and quiet_hours_end'),

      spacer(200),
      new Paragraph({ children: [new PageBreak()] }),

      // ── 5. MODULE BREAKDOWN ────────────────────────────────
      h1('5. Module Breakdown'),
      spacer(80),

      sectionDivider('5.1  Infrastructure & Database', COLORS.lavender, COLORS.lavPale),
      spacer(80),
      statusTable([
        ['PostgreSQL 16 setup', 'Database running via Homebrew on macOS', 'done'],
        ['pgvector extension', 'Vector search enabled, 1536-dim embeddings ready', 'done'],
        ['15-table schema', 'All tables created with indexes, triggers, cascade deletes', 'done'],
        ['ENUM types', 'All custom PG enums defined (persona_style, goal_type, flag_type, etc.)', 'done'],
        ['Auto-timestamp triggers', 'updated_at auto-updated on all relevant tables', 'done'],
        ['pg_cron setup', 'Schema stubs ready, activation pending scheduler endpoints', 'partial'],
      ]),
      spacer(160),

      sectionDivider('5.2  FastAPI Backend', COLORS.teal, COLORS.tealPale),
      spacer(80),
      statusTable([
        ['Project skeleton', 'FastAPI app, folder structure, venv, .env, requirements.txt', 'done'],
        ['Async DB connection', 'SQLAlchemy async engine + session factory via db.py', 'done'],
        ['SQLAlchemy models', 'models/user.py + models/log.py covering all 15 tables', 'done'],
        ['POST /users/onboard', 'Creates user + health profile + persona config + scheduler state in one transaction', 'done'],
        ['GET /users/{user_id}', 'Fetch full user record by UUID', 'done'],
        ['POST /logs/daily', 'Upsert daily log — weight, nutrition, mood, sleep, pain flags', 'done'],
        ['POST /logs/meal', 'Log individual meal, auto-updates daily nutrition totals', 'done'],
        ['POST /logs/workout', 'Log workout session with HR data, exercises JSONB, pain flag', 'done'],
        ['GET /logs/daily/{user_id}/{date}', 'Fetch a full daily log by user and date', 'done'],
        ['GET / and GET /health', 'Health check endpoints', 'done'],
      ]),
      spacer(160),

      sectionDivider('5.3  AI / Claude Integration', COLORS.sage, COLORS.sagePale),
      spacer(80),
      statusTable([
        ['POST /chat', 'Main conversational endpoint — user sends message, Claude responds in persona', 'done'],
        ['Context assembly', 'Load user profile + today\'s log + persona + last 10 messages', 'done'],
        ['RAG retrieval', 'Semantic search over rag_documents using pgvector cosine similarity', 'done'],
        ['Orchestrator system prompt', 'Build dynamic system prompt with user context + persona + date/time', 'done'],
        ['Claude API call', 'anthropic.messages.create() with assembled context + system prompt', 'done'],
        ['Nutrition Bot routing', 'Detect nutrition intent, build specialist prompt, call Claude again', 'done'],
        ['Training Bot routing', 'Detect training intent, build specialist prompt, call Claude again', 'done'],
        ['Reporting Engine', 'Aggregate log data, generate structured weekly/monthly report', 'todo'],
        ['Safety escalation layer', 'Override persona on pain/distress signals, always-on', 'todo'],
        ['Message persistence', 'Save user + assistant messages, persona_applied, token_count to DB', 'done'],
        ['Embedding generation', 'Generate ada-002 embeddings for RAG document inserts', 'done'],
      ]),
      spacer(160),

      sectionDivider('5.4  Persona Engine', COLORS.amber, COLORS.amberPale),
      spacer(80),
      statusTable([
        ['Persona config table', 'user_persona_configs table created and populated on onboarding', 'done'],
        ['Persona switch log', 'persona_switch_log table ready for audit trail', 'done'],
        ['Warm Friend prompt', 'System prompt defined in project knowledge', 'done'],
        ['Structured Coach prompt', 'System prompt defined in project knowledge', 'done'],
        ['Commander prompt', 'System prompt defined in project knowledge', 'done'],
        ['Persona injection into Claude calls', 'Pass active_persona into Orchestrator system prompt on every call', 'done'],
        ['POST /persona/switch', 'Allow user to switch persona mid-session with logging', 'todo'],
        ['Safety override enforcement', 'Override all personas on medical/pain/distress flags', 'todo'],
      ]),
      spacer(160),

      sectionDivider('5.5  Scheduler & Notifications', COLORS.sky, COLORS.skyPale),
      spacer(80),
      statusTable([
        ['user_scheduler_state table', 'Scheduler state table created on onboarding with defaults', 'done'],
        ['nudge_log table', 'Ready to receive nudge records', 'done'],
        ['POST /scheduler/checkin', 'Trigger a daily check-in for a user (called by pg_cron)', 'todo'],
        ['POST /scheduler/nudge', 'Send a nudge via WhatsApp or in-app', 'todo'],
        ['Twilio WhatsApp integration', 'Send messages via Twilio API', 'todo'],
        ['pg_cron jobs', 'Activate cron jobs after scheduler endpoints are built', 'todo'],
        ['Quiet hours enforcement', 'Suppress nudges during quiet_hours_start to quiet_hours_end', 'todo'],
        ['Weekly report trigger', 'Auto-generate and deliver weekly report on schedule', 'todo'],
      ]),
      spacer(160),

      sectionDivider('5.6  Reporting Engine', COLORS.rose, COLORS.rosePale),
      spacer(80),
      statusTable([
        ['reports table', 'Ready to store report snapshots as JSONB', 'done'],
        ['GET /reports/weekly/{user_id}', 'Generate or retrieve weekly progress report', 'todo'],
        ['GET /reports/monthly/{user_id}', 'Generate or retrieve monthly summary report', 'todo'],
        ['Data aggregation logic', 'Aggregate daily_logs, meal_logs, workout_logs over report period', 'todo'],
        ['Claude report narrative', 'Pass aggregated data to Claude for written summary in persona voice', 'todo'],
        ['Trend analysis', 'Compare current period vs previous period for weight, calories, workouts', 'todo'],
      ]),
      spacer(160),

      sectionDivider('5.7  Frontend', COLORS.accent, COLORS.accentPale),
      spacer(80),
      statusTable([
        ['Next.js project setup', 'Create Next.js app, routing, Tailwind', 'todo'],
        ['Google / Apple SSO', 'Auth flow, token exchange, call /users/onboard', 'todo'],
        ['Onboarding flow (8 steps)', 'Conversational onboarding collecting all profile data', 'todo'],
        ['Dashboard', 'Today\'s log summary, streak, weight chart, quick log buttons', 'todo'],
        ['Chat interface', 'Conversational UI calling POST /chat', 'todo'],
        ['Log entry screens', 'Meal log, workout log, daily check-in forms', 'todo'],
        ['Persona selector', 'UI to switch between Friend / Coach / Commander', 'todo'],
        ['Reports screen', 'Display weekly and monthly report data', 'todo'],
      ]),

      spacer(200),
      new Paragraph({ children: [new PageBreak()] }),

      // ── 6. WHAT'S NEXT ─────────────────────────────────────
      h1('6. Immediate Roadmap'),
      spacer(80),

      h2('Day 4 — Claude Integration ✅ COMPLETE'),
      bullet('POST /chat endpoint — context assembly, Claude API call, persona-voiced response'),
      bullet('Messages saved to DB with persona_applied and token_count'),
      bullet('Hebrew response confirmed — language preference respected'),
      bullet('Conversation + message tables rebuilt and working'),
      spacer(60),

      h2('Day 5 — Specialist Bots + RAG ✅ COMPLETE'),
      bullet('RAG service — ada-002 embeddings, pgvector cosine search, top-K retrieval'),
      bullet('seed_rag.py — 6 global wellness docs seeded (nutrition x2, training x2, safety x2)'),
      bullet('Nutrition Bot — specialist Claude call, RAG-aware, routes on nutrition intent'),
      bullet('Training Bot — specialist Claude call, RAG-aware, routes on training/HR intent'),
      bullet('Intent detection — classifies every message as nutrition / training / general'),
      spacer(60),

      h2('Day 6 — Frontend Skeleton'),
      bullet('Next.js project setup'),
      bullet('Google SSO integration'),
      bullet('Basic onboarding flow (steps 1-4)'),
      bullet('Chat UI wired to POST /chat'),
      spacer(60),

      h2('Day 7 — Scheduler + Notifications'),
      bullet('Twilio WhatsApp integration'),
      bullet('POST /scheduler/checkin and POST /scheduler/nudge'),
      bullet('Activate pg_cron jobs'),
      bullet('Quiet hours enforcement'),
      spacer(60),

      h2('Day 8 — Reporting Engine'),
      bullet('Data aggregation queries'),
      bullet('Claude-generated weekly narrative'),
      bullet('Report delivery via WhatsApp'),
      spacer(60),

      h2('Day 9-10 — Polish & MVP Wrap'),
      bullet('Safety escalation layer full testing'),
      bullet('Persona switch endpoint + UI'),
      bullet('End-to-end flow testing with real user data'),
      bullet('Hosting decision and deployment prep'),

      spacer(200),

      // ── 7. KEY DESIGN DECISIONS ────────────────────────────
      h1('7. Key Design Decisions'),
      spacer(80),

      h2('No password auth'),
      para('Google and Apple SSO only. Phone number is nullable and only collected when user opts into WhatsApp nudges. Reduces friction and eliminates password management complexity.'),
      spacer(60),

      h2('Plans are versioned by appending, not updating'),
      para('When a nutrition or training plan is updated, a new row is inserted and the old one is archived (status = "archived"). This preserves history and enables trend comparison without destructive updates.'),
      spacer(60),

      h2('Safety override is always-on'),
      para('Regardless of the active persona, the system must detect pain signals, medical flags, and emotional distress and route to an empathetic safety response. The Commander persona cannot shame users about medical issues or push through injury. This is hardcoded, not configurable.'),
      spacer(60),

      h2('Daily log uses upsert pattern'),
      para('POST /logs/daily creates a new daily_log row if none exists for that date, or updates the existing one. This means the frontend can call it incrementally throughout the day without worrying about duplicates.'),
      spacer(60),

      h2('Raw Claude response stored as JSONB'),
      para('Every message stores the complete Claude API response object in messages.raw_bot_response. This enables debugging, token tracking, and future reprocessing without re-calling the API.'),
      spacer(60),

      h2('Meal logs auto-accumulate into daily totals'),
      para('When a meal log is created, the service layer immediately adds its calories and macros to the parent daily_log totals. This means the dashboard always shows up-to-date daily nutrition without requiring a separate aggregation query.'),

      spacer(240),

      // ── FOOTER ─────────────────────────────────────────────
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [9360],
        rows: [new TableRow({ children: [
          new TableCell({
            borders: { top: { style: BorderStyle.SINGLE, size: 4, color: COLORS.sageLight }, bottom: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' }, left: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' }, right: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' } },
            margins: { top: 120, bottom: 0, left: 0, right: 0 },
            children: [new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [new TextRun({ text: 'VitaCompanion  ·  Confidential  ·  MVP v1.0  ·  March 2026', size: 18, color: COLORS.muted, font: 'Arial' })]
            })]
          })
        ]})]
      }),

    ]
  },
  // ── SECTION 2: FLOWCHART PAGE (LANDSCAPE) ─────────────────
  {
    properties: {
      page: {
        size: { width: 15840, height: 12240 }, // Landscape US Letter
        margin: { top: 720, right: 720, bottom: 720, left: 720 }
      }
    },
    children: [
      new Paragraph({
        spacing: { before: 0, after: 100 },
        children: [
          new TextRun({ text: 'Appendix A — System Data Flow', bold: true, size: 36, color: COLORS.sage, font: 'Arial' }),
        ]
      }),
      new Paragraph({
        spacing: { before: 0, after: 200 },
        children: [new TextRun({
          text: 'End-to-end data flow across all 7 layers: User Layer → API Gateway → Orchestrator (Claude) → Specialist Bots → Data Layer → Scheduler → Notifications. Dashed lines indicate async or background flows.',
          size: 20, color: COLORS.muted, font: 'Arial', italics: true
        })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          new ImageRun({
            type: 'png',
            data: flowchartPng,
            transformation: { width: 1380, height: 816 },
            altText: { title: 'VitaCompanion System Data Flow', description: 'Architecture flowchart showing all modules and data flows', name: 'flowchart' }
          })
        ]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 160, after: 0 },
        children: [new TextRun({ text: 'VitaCompanion  ·  Confidential  ·  MVP v1.0  ·  March 2026', size: 18, color: COLORS.muted, font: 'Arial' })]
      }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('/home/claude/VitaCompanion_PRD.docx', buffer);
  console.log('Done', buffer.length, 'bytes');
});
