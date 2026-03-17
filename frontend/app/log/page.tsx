"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const DEV_USER_ID = "9f6e1f8c-bf14-4e26-9497-836704795ab2";

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

interface DailyLogData {
  weight_kg: number | null;
  calories_total: number | null;
  protein_g: number | null;
  energy_level: number | null;
  mood_score: number | null;
  sleep_hours: number | null;
  workout_completed: boolean | null;
  notes: string | null;
}

function ScaleRow({
  label,
  max,
  value,
  onChange,
}: {
  label: string;
  max: number;
  value: number | null;
  onChange: (v: number) => void;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <div className="flex gap-2">
        {Array.from({ length: max }, (_, i) => i + 1).map((n) => (
          <button
            key={n}
            type="button"
            onClick={() => onChange(n)}
            className={`w-9 h-9 rounded-lg text-sm font-medium border transition-colors ${
              value === n
                ? "bg-blue-600 text-white border-blue-600"
                : "border-gray-300 text-gray-600 hover:border-blue-400"
            }`}
          >
            {n}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function LogPage() {
  const today = todayISO();

  // Resolve user ID — try sync endpoint first, fall back to dev
  const [userId, setUserId] = useState(DEV_USER_ID);
  useEffect(() => {
    fetch("/api/auth/sync", { method: "POST" })
      .then((r) => r.ok ? r.json() : null)
      .then((d) => { if (d?.user_id) setUserId(d.user_id); })
      .catch(() => {});
  }, []);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState<DailyLogData>({
    weight_kg: null,
    calories_total: null,
    protein_g: null,
    energy_level: null,
    mood_score: null,
    sleep_hours: null,
    workout_completed: null,
    notes: null,
  });

  // Load today's existing log
  useEffect(() => {
    setLoading(true);
    fetch(`${API_URL}/logs/daily/${userId}/${today}`)
      .then((r) => r.ok ? r.json() : null)
      .then((data) => {
        if (data) {
          setForm({
            weight_kg: data.weight_kg,
            calories_total: data.calories_total,
            protein_g: data.protein_g,
            energy_level: data.energy_level,
            mood_score: data.mood_score,
            sleep_hours: data.sleep_hours,
            workout_completed: data.workout_completed,
            notes: data.notes,
          });
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [userId, today]);

  function setField<K extends keyof DailyLogData>(key: K, value: DailyLogData[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setSaved(false);
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSaved(false);

    try {
      const res = await fetch(`${API_URL}/logs/daily`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          log_date: today,
          ...form,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
        throw new Error(err.detail ?? `HTTP ${res.status}`);
      }
      setSaved(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setSaving(false);
    }
  }

  const displayDate = new Date().toLocaleDateString("en-US", {
    weekday: "long", month: "long", day: "numeric",
  });

  return (
    <main className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-6 py-4 flex items-center gap-4">
        <Link href="/dashboard" className="text-gray-400 hover:text-gray-700 text-sm">
          ← Dashboard
        </Link>
        <span className="text-lg font-semibold text-gray-900">Today&apos;s Log</span>
        <span className="text-sm text-gray-400 ml-auto">{displayDate}</span>
      </nav>

      <div className="max-w-lg mx-auto px-6 py-8">
        {loading ? (
          <div className="flex justify-center py-16">
            <svg className="animate-spin w-6 h-6 text-blue-500" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
          </div>
        ) : (
          <form onSubmit={handleSave} className="flex flex-col gap-6">

            {/* Weight */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Weight (kg)</label>
              <input
                type="number"
                min={30}
                max={300}
                step={0.1}
                placeholder="e.g. 75.5"
                value={form.weight_kg ?? ""}
                onChange={(e) => setField("weight_kg", e.target.value ? parseFloat(e.target.value) : null)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Sleep */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Sleep (hours)</label>
              <input
                type="number"
                min={0}
                max={24}
                step={0.5}
                placeholder="e.g. 7.5"
                value={form.sleep_hours ?? ""}
                onChange={(e) => setField("sleep_hours", e.target.value ? parseFloat(e.target.value) : null)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Energy & Mood */}
            <ScaleRow
              label="Energy level (1–5)"
              max={5}
              value={form.energy_level}
              onChange={(v) => setField("energy_level", v)}
            />
            <ScaleRow
              label="Mood (1–5)"
              max={5}
              value={form.mood_score}
              onChange={(v) => setField("mood_score", v)}
            />

            {/* Workout */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Workout</label>
              <div className="flex gap-3">
                {[
                  { value: true,  label: "✓ Done" },
                  { value: false, label: "✗ Skipped" },
                  { value: null,  label: "— Not yet" },
                ].map(({ value, label }) => (
                  <button
                    key={String(value)}
                    type="button"
                    onClick={() => setField("workout_completed", value)}
                    className={`flex-1 py-2 rounded-lg text-sm border transition-colors ${
                      form.workout_completed === value
                        ? "bg-blue-600 text-white border-blue-600"
                        : "border-gray-300 text-gray-600 hover:border-blue-400"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Notes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
              <textarea
                rows={3}
                placeholder="Anything else about your day…"
                value={form.notes ?? ""}
                onChange={(e) => setField("notes", e.target.value || null)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
            </div>

            {error && <p className="text-sm text-red-500">{error}</p>}
            {saved && <p className="text-sm text-green-600">Log saved!</p>}

            <button
              type="submit"
              disabled={saving}
              className="w-full bg-blue-600 text-white font-medium py-3 rounded-xl hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {saving ? "Saving…" : "Save log"}
            </button>
          </form>
        )}
      </div>
    </main>
  );
}
