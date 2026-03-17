"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Persona = "friend" | "coach" | "commander";
type Goal = "weight_loss" | "muscle_gain" | "maintenance" | "endurance" | "general_health";

const GOAL_LABELS: Record<Goal, string> = {
  weight_loss: "Lose weight",
  muscle_gain: "Build muscle",
  maintenance: "Maintain weight",
  endurance: "Improve endurance",
  general_health: "General health",
};

const PERSONA_LABELS: Record<Persona, { label: string; desc: string }> = {
  friend:    { label: "Friend",    desc: "Warm & encouraging" },
  coach:     { label: "Coach",     desc: "Direct & data-driven" },
  commander: { label: "Commander", desc: "Tough & no-excuses" },
};

export default function OnboardPage() {
  const { data: session } = useSession();
  const router = useRouter();

  const [form, setForm] = useState({
    date_of_birth: "",
    sex: "other" as "male" | "female" | "other",
    height_cm: "",
    starting_weight_kg: "",
    primary_goal: "general_health" as Goal,
    persona: "friend" as Persona,
    language: "en",
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function set<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const payload = {
        email: session?.user?.email ?? "unknown@example.com",
        full_name: session?.user?.name ?? "New User",
        sso_provider: "google",
        sso_id: session?.user?.email ?? `anon-${Date.now()}`,
        avatar_url: session?.user?.image ?? null,
        date_of_birth: form.date_of_birth,
        sex: form.sex,
        height_cm: parseFloat(form.height_cm),
        starting_weight_kg: parseFloat(form.starting_weight_kg),
        primary_goal: form.primary_goal,
        persona: form.persona,
        language: form.language,
        timezone: form.timezone,
      };

      const res = await fetch(`${API_URL}/users/onboard`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
        throw new Error(err.detail ?? `HTTP ${res.status}`);
      }

      router.push("/chat");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-md bg-white rounded-2xl border border-gray-200 p-8 shadow-sm">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Welcome to VitaCompanion</h1>
        <p className="text-sm text-gray-500 mb-8">
          Hi {session?.user?.name?.split(" ")[0] ?? "there"}! Just a few details to get started.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          {/* Date of birth */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Date of birth</label>
            <input
              type="date"
              required
              value={form.date_of_birth}
              onChange={(e) => set("date_of_birth", e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Sex */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sex</label>
            <select
              value={form.sex}
              onChange={(e) => set("sex", e.target.value as typeof form.sex)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other / prefer not to say</option>
            </select>
          </div>

          {/* Height & weight side by side */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Height (cm)</label>
              <input
                type="number"
                required
                min={100}
                max={250}
                step={0.1}
                placeholder="170"
                value={form.height_cm}
                onChange={(e) => set("height_cm", e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Weight (kg)</label>
              <input
                type="number"
                required
                min={30}
                max={300}
                step={0.1}
                placeholder="75"
                value={form.starting_weight_kg}
                onChange={(e) => set("starting_weight_kg", e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Primary goal */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Primary goal</label>
            <select
              value={form.primary_goal}
              onChange={(e) => set("primary_goal", e.target.value as Goal)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {(Object.keys(GOAL_LABELS) as Goal[]).map((g) => (
                <option key={g} value={g}>{GOAL_LABELS[g]}</option>
              ))}
            </select>
          </div>

          {/* Persona */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Coaching style</label>
            <div className="grid grid-cols-3 gap-2">
              {(Object.keys(PERSONA_LABELS) as Persona[]).map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => set("persona", p)}
                  className={`rounded-xl border px-3 py-3 text-left transition-colors ${
                    form.persona === p
                      ? "border-blue-500 bg-blue-50 text-blue-800"
                      : "border-gray-200 text-gray-600 hover:border-gray-400"
                  }`}
                >
                  <div className="text-sm font-semibold">{PERSONA_LABELS[p].label}</div>
                  <div className="text-xs mt-0.5">{PERSONA_LABELS[p].desc}</div>
                </button>
              ))}
            </div>
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-blue-600 text-white font-medium py-3 rounded-xl hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {submitting ? "Setting up your account…" : "Get started"}
          </button>
        </form>
      </div>
    </main>
  );
}
