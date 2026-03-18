"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Types ──────────────────────────────────────────────────────────

type Goal = "weight_loss" | "muscle_gain" | "general_health" | "endurance" | "maintenance";
type Activity = "sedentary" | "light" | "moderate" | "active" | "very_active";
type Persona = "friend" | "coach" | "commander";

interface FormState {
  // Step 1 — Goal
  primary_goal: Goal;
  // Step 2 — Vitals
  date_of_birth: string;
  sex: "male" | "female" | "other";
  height_cm: string;
  starting_weight_kg: string;
  activity_level: Activity;
  // Step 3 — Medical (optional)
  medical_conditions: string;
  medications: string;
  // Step 4 — Dietary (optional)
  dietary_restrictions: string;
  // Step 5 — Persona
  persona: Persona;
}

// ── Step configs ───────────────────────────────────────────────────

const GOALS: { value: Goal; label: string; desc: string }[] = [
  { value: "weight_loss",   label: "Lose weight",        desc: "Sustainable fat loss through nutrition and activity" },
  { value: "muscle_gain",   label: "Build muscle",        desc: "Strength training with adequate protein intake" },
  { value: "general_health",label: "General health",      desc: "Feel better, move more, age well" },
  { value: "endurance",     label: "Improve endurance",   desc: "Cardio fitness and stamina" },
  { value: "maintenance",   label: "Maintain weight",     desc: "Stay at your current weight and fitness level" },
];

const ACTIVITY_LEVELS: { value: Activity; label: string; desc: string }[] = [
  { value: "sedentary",   label: "Sedentary",    desc: "Desk job, little to no exercise" },
  { value: "light",       label: "Light",        desc: "Light exercise 1–3 days/week" },
  { value: "moderate",    label: "Moderate",     desc: "Moderate exercise 3–5 days/week" },
  { value: "active",      label: "Active",       desc: "Hard exercise 6–7 days/week" },
  { value: "very_active", label: "Very active",  desc: "Hard daily exercise or physical job" },
];

const PERSONAS: { value: Persona; label: string; desc: string }[] = [
  { value: "friend",    label: "Friend",    desc: "Warm, encouraging, non-judgmental" },
  { value: "coach",     label: "Coach",     desc: "Direct, data-driven, goal-focused" },
  { value: "commander", label: "Commander", desc: "Tough, intense, no excuses" },
];

const TOTAL_STEPS = 5;

// ── Helpers ────────────────────────────────────────────────────────

function splitCSV(s: string): string[] {
  return s.split(",").map((x) => x.trim()).filter(Boolean);
}

function StepIndicator({ current }: { current: number }) {
  return (
    <div className="flex items-center gap-1 mb-8">
      {Array.from({ length: TOTAL_STEPS }, (_, i) => (
        <div
          key={i}
          className={`h-1.5 flex-1 rounded-full transition-colors ${
            i < current ? "bg-blue-600" : i === current ? "bg-blue-300" : "bg-gray-200"
          }`}
        />
      ))}
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────

export default function OnboardingPage() {
  const { data: session } = useSession();
  const router = useRouter();

  const [step, setStep] = useState(0);
  const [form, setForm] = useState<FormState>({
    primary_goal: "general_health",
    date_of_birth: "",
    sex: "other",
    height_cm: "",
    starting_weight_kg: "",
    activity_level: "moderate",
    medical_conditions: "",
    medications: "",
    dietary_restrictions: "",
    persona: "friend",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function set<K extends keyof FormState>(key: K, val: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: val }));
  }

  function canAdvance(): boolean {
    if (step === 1) {
      return (
        !!form.date_of_birth &&
        !!form.height_cm &&
        !!form.starting_weight_kg
      );
    }
    return true;
  }

  async function handleSubmit() {
    setSubmitting(true);
    setError(null);
    try {
      // Use the stable Google sub as sso_id; fall back to email only if sub is absent
      // (e.g. dev bypass without a real Google session)
      const ssoId = (session as { googleSub?: string } & typeof session)?.googleSub
        ?? session?.user?.email
        ?? `anon-${Date.now()}`;

      const payload = {
        email: session?.user?.email ?? "unknown@example.com",
        full_name: session?.user?.name ?? "New User",
        sso_provider: "google",
        sso_id: ssoId,
        avatar_url: session?.user?.image ?? null,
        date_of_birth: form.date_of_birth,
        sex: form.sex,
        height_cm: parseFloat(form.height_cm),
        starting_weight_kg: parseFloat(form.starting_weight_kg),
        primary_goal: form.primary_goal,
        activity_level: form.activity_level,
        medical_conditions: splitCSV(form.medical_conditions),
        medications: splitCSV(form.medications),
        dietary_restrictions: splitCSV(form.dietary_restrictions),
        persona: form.persona,
        language: "en",
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      };

      console.log("[onboarding] POST /users/onboard payload:", payload);

      const res = await fetch(`${API_URL}/users/onboard`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const responseBody = await res.json().catch(() => null);
      console.log("[onboarding] response status:", res.status, "body:", responseBody);

      if (!res.ok) {
        throw new Error(responseBody?.detail ?? `HTTP ${res.status}`);
      }

      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setSubmitting(false);
    }
  }

  const heading = [
    "What's your primary goal?",
    "Tell us about yourself",
    "Any medical context?",
    "Dietary preferences?",
    "Choose your coaching style",
  ][step];

  const subheading = [
    "We'll tailor your coaching to what matters most to you.",
    "Used to personalise your nutrition and training targets.",
    "Helps your coach give safer, smarter advice.",
    "We'll factor these into meal and snack suggestions.",
    "You can change this anytime from the chat page.",
  ][step];

  const isOptionalStep = step === 2 || step === 3;

  return (
    <main className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg bg-white rounded-2xl border border-gray-200 p-8 shadow-sm">

        <StepIndicator current={step} />

        <h1 className="text-2xl font-bold text-gray-900 mb-1">{heading}</h1>
        {isOptionalStep && (
          <p className="text-xs text-gray-400 mb-1">(Optional)</p>
        )}
        <p className="text-sm text-gray-500 mb-6">{subheading}</p>

        {/* ── Step 0: Goal ── */}
        {step === 0 && (
          <div className="flex flex-col gap-3">
            {GOALS.map((g) => (
              <button
                key={g.value}
                type="button"
                onClick={() => set("primary_goal", g.value)}
                className={`text-left rounded-xl border px-4 py-3 transition-colors ${
                  form.primary_goal === g.value
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-200 hover:border-gray-400"
                }`}
              >
                <div className="text-sm font-semibold text-gray-800">{g.label}</div>
                <div className="text-xs text-gray-500 mt-0.5">{g.desc}</div>
              </button>
            ))}
          </div>
        )}

        {/* ── Step 1: Vitals ── */}
        {step === 1 && (
          <div className="flex flex-col gap-4">
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
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Sex</label>
              <select
                value={form.sex}
                onChange={(e) => set("sex", e.target.value as FormState["sex"])}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other / prefer not to say</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Height (cm)</label>
                <input
                  type="number" min={100} max={250} step={0.1} placeholder="170"
                  value={form.height_cm}
                  onChange={(e) => set("height_cm", e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Weight (kg)</label>
                <input
                  type="number" min={30} max={300} step={0.1} placeholder="75"
                  value={form.starting_weight_kg}
                  onChange={(e) => set("starting_weight_kg", e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Activity level</label>
              <div className="flex flex-col gap-2">
                {ACTIVITY_LEVELS.map((a) => (
                  <button
                    key={a.value}
                    type="button"
                    onClick={() => set("activity_level", a.value)}
                    className={`text-left rounded-xl border px-4 py-2.5 transition-colors ${
                      form.activity_level === a.value
                        ? "border-blue-500 bg-blue-50"
                        : "border-gray-200 hover:border-gray-400"
                    }`}
                  >
                    <span className="text-sm font-medium text-gray-800">{a.label}</span>
                    <span className="text-xs text-gray-500 ml-2">{a.desc}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── Step 2: Medical ── */}
        {step === 2 && (
          <div className="flex flex-col gap-4">
            <p className="text-xs text-gray-400">Enter as comma-separated values, e.g. type2_diabetes, hypertension</p>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Medical conditions</label>
              <input
                type="text"
                placeholder="e.g. type2_diabetes, hypertension"
                value={form.medical_conditions}
                onChange={(e) => set("medical_conditions", e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Medications</label>
              <input
                type="text"
                placeholder="e.g. metformin, lisinopril"
                value={form.medications}
                onChange={(e) => set("medications", e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        )}

        {/* ── Step 3: Dietary ── */}
        {step === 3 && (
          <div className="flex flex-col gap-4">
            <p className="text-xs text-gray-400">Enter as comma-separated values</p>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Dietary restrictions</label>
              <input
                type="text"
                placeholder="e.g. gluten_free, lactose_intolerant, vegetarian"
                value={form.dietary_restrictions}
                onChange={(e) => set("dietary_restrictions", e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        )}

        {/* ── Step 4: Persona ── */}
        {step === 4 && (
          <div className="flex flex-col gap-3">
            {PERSONAS.map((p) => (
              <button
                key={p.value}
                type="button"
                onClick={() => set("persona", p.value)}
                className={`text-left rounded-xl border px-4 py-3 transition-colors ${
                  form.persona === p.value
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-200 hover:border-gray-400"
                }`}
              >
                <div className="text-sm font-semibold text-gray-800">{p.label}</div>
                <div className="text-xs text-gray-500 mt-0.5">{p.desc}</div>
              </button>
            ))}
          </div>
        )}

        {error && <p className="text-sm text-red-500 mt-4">{error}</p>}

        {/* Navigation */}
        <div className="flex gap-3 mt-8">
          {step > 0 && (
            <button
              type="button"
              onClick={() => setStep((s) => s - 1)}
              className="flex-1 py-3 rounded-xl border border-gray-300 text-sm text-gray-600 hover:bg-gray-50 transition-colors"
            >
              Back
            </button>
          )}

          {step < TOTAL_STEPS - 1 ? (
            <button
              type="button"
              disabled={!canAdvance()}
              onClick={() => setStep((s) => s + 1)}
              className="flex-1 bg-blue-600 text-white font-medium py-3 rounded-xl hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Next
            </button>
          ) : (
            <button
              type="button"
              disabled={submitting}
              onClick={handleSubmit}
              className="flex-1 bg-blue-600 text-white font-medium py-3 rounded-xl hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {submitting ? "Setting up your account…" : "Get started"}
            </button>
          )}
        </div>

        <p className="text-xs text-center text-gray-400 mt-4">
          Step {step + 1} of {TOTAL_STEPS}
        </p>
      </div>
    </main>
  );
}
