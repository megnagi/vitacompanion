"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import ChatMessage from "@/components/ChatMessage";

interface Message {
  role: "user" | "assistant";
  content: string;
}

type Persona = "friend" | "coach" | "commander";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const DEV_USER_ID = "9f6e1f8c-bf14-4e26-9497-836704795ab2";

const PERSONA_LABELS: Record<Persona, string> = {
  friend: "Friend",
  coach: "Coach",
  commander: "Commander",
};

export default function ChatPage() {
  const { data: session, status: authStatus } = useSession();
  const router = useRouter();

  const [userId, setUserId] = useState<string>(DEV_USER_ID);
  const [userName, setUserName] = useState<string>("Test User");
  const [activePersona, setActivePersona] = useState<Persona>("friend");
  const [personaLoaded, setPersonaLoaded] = useState(false); // true once DB persona is known

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [waiting, setWaiting] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [switchingPersona, setSwitchingPersona] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);

  // Resolve real user from session; redirect to /onboard if user not found
  useEffect(() => {
    if (authStatus === "loading") return;

    if (authStatus === "unauthenticated") {
      // Dev bypass: use DEV_USER_ID without SSO
      setPersonaLoaded(true);
      return;
    }

    fetch("/api/auth/sync", { method: "POST" })
      .then((r) => ({ status: r.status, body: r.json() }))
      .then(async ({ status, body }) => {
        const data = await body;
        if (status === 404) {
          router.replace("/onboarding");
          return;
        }
        if (data.user_id) {
          setUserId(data.user_id);
          setUserName(data.full_name ?? session?.user?.name ?? "");
          setActivePersona((data.persona as Persona) ?? "friend");
        }
        setPersonaLoaded(true);
      })
      .catch(() => setPersonaLoaded(true));
  }, [authStatus, session, router]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, waiting, streaming]);

  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || waiting || streaming) return;

    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setWaiting(true);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          message: text,
          conversation_id: conversationId,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
        throw new Error(err.detail ?? `HTTP ${res.status}`);
      }

      if (!res.body) throw new Error("No response body");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let firstChunk = true;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const payload = JSON.parse(line.slice(6));

          if (payload.chunk) {
            if (firstChunk) {
              firstChunk = false;
              setWaiting(false);
              setStreaming(true);
              setMessages((prev) => [...prev, { role: "assistant", content: payload.chunk }]);
            } else {
              setMessages((prev) => {
                const next = [...prev];
                next[next.length - 1] = {
                  role: "assistant",
                  content: next[next.length - 1].content + payload.chunk,
                };
                return next;
              });
            }
          } else if (payload.done) {
            if (payload.conversation_id) setConversationId(payload.conversation_id);
          }
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setWaiting(false);
      setStreaming(false);
    }
  }, [input, waiting, streaming, userId, conversationId]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  async function handlePersonaSwitch(persona: Persona) {
    if (persona === activePersona || switchingPersona) return;
    setSwitchingPersona(true);
    try {
      const res = await fetch(`${API_URL}/users/${userId}/persona/switch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ persona }),
      });
      if (res.ok) setActivePersona(persona);
    } catch {
      // silently ignore — UI stays on current persona
    } finally {
      setSwitchingPersona(false);
    }
  }

  const busy = waiting || streaming;
  const firstName = userName.split(" ")[0];

  return (
    <main className="min-h-screen bg-gray-50 flex flex-col">
      {/* Nav */}
      <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-4 shrink-0">
        <Link href="/dashboard" className="text-gray-400 hover:text-gray-700 text-sm">
          ← Dashboard
        </Link>
        <span className="text-lg font-semibold text-gray-900 flex-1">
          VitaCompanion
          {firstName && (
            <span className="text-base font-normal text-gray-500 ml-2">· {firstName}</span>
          )}
        </span>

        {/* Persona switcher — hidden until DB persona is loaded to avoid flicker */}
        {personaLoaded && (
          <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
            {(Object.keys(PERSONA_LABELS) as Persona[]).map((p) => (
              <button
                key={p}
                onClick={() => handlePersonaSwitch(p)}
                disabled={switchingPersona}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                  activePersona === p
                    ? "bg-white text-blue-700 shadow-sm"
                    : "text-gray-500 hover:text-gray-800"
                }`}
              >
                {PERSONA_LABELS[p]}
              </button>
            ))}
          </div>
        )}
      </nav>

      {/* Message list */}
      <div className="flex-1 overflow-y-auto px-4 py-6 flex flex-col gap-3 max-w-2xl w-full mx-auto">
        {messages.length === 0 && !waiting && (
          <p className="text-center text-gray-400 text-sm mt-16">
            Ask me about nutrition, workouts, or how your day went.
          </p>
        )}

        {messages.map((msg, i) => (
          <ChatMessage key={i} role={msg.role} content={msg.content} />
        ))}

        {waiting && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-4 py-3 flex gap-1 items-center">
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" />
            </div>
          </div>
        )}

        {error && <p className="text-center text-red-500 text-sm">{error}</p>}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-200 px-4 py-4 shrink-0">
        <div className="max-w-2xl mx-auto flex gap-3 items-end">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message your coach… (Enter to send)"
            rows={1}
            className="flex-1 resize-none border border-gray-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={sendMessage}
            disabled={busy || !input.trim()}
            className="px-5 py-3 bg-blue-600 text-white text-sm font-medium rounded-xl hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {streaming ? "…" : "Send"}
          </button>
        </div>
      </div>
    </main>
  );
}
