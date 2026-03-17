# VitaCompanion Frontend — Claude Code Context

Next.js 14 App Router + TypeScript + Tailwind. Runs on http://localhost:3000.

## Key Facts
- API base: `http://localhost:8000` (via `NEXT_PUBLIC_API_URL` env var, defaults to localhost)
- `DEV_USER_ID` is hardcoded in `app/chat/page.tsx` — replace with real auth on Day 9
- Auth is bypassed for dev: `/chat` and `/dashboard` are accessible without SSO
- Chat uses SSE streaming via `fetch()` + `ReadableStream` — not axios, not WebSocket

## Chat Streaming Pattern
`POST /chat` returns `text/event-stream`. Each line is:
```
data: {"chunk": "text..."}   ← append to last message bubble
data: {"done": true, "conversation_id": "..."}  ← stream complete
```
The frontend uses two states: `waiting` (typing indicator) and `streaming` (chunks arriving).

## File Map
```
app/
  page.tsx              # Landing — Google sign-in + "Continue as test user" link
  chat/page.tsx         # SSE streaming chat UI
  dashboard/page.tsx    # Dashboard (no auth gate)
  layout.tsx            # Wraps in <Providers> (SessionProvider)
  providers.tsx         # "use client" SessionProvider
  api/auth/[...nextauth]/route.ts  # next-auth v4 Google provider
components/
  ChatMessage.tsx       # Renders user/assistant bubbles
```
