"use client";

import Link from "next/link";

export default function DashboardPage() {
  const today = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  const firstName = "Test";

  return (
    <main className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <span className="text-xl font-bold text-gray-900">VitaCompanion</span>
        <Link href="/" className="text-sm text-gray-500 hover:text-gray-800">
          Sign out
        </Link>
      </nav>

      <div className="max-w-2xl mx-auto px-6 py-12 flex flex-col gap-6">
        <div>
          <p className="text-sm text-gray-500">{today}</p>
          <h1 className="text-3xl font-bold text-gray-900 mt-1">
            Welcome back, {firstName}!
          </h1>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Link
            href="/chat"
            className="block bg-white rounded-xl border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            <h2 className="text-lg font-semibold text-gray-800 mb-1">Chat with Coach</h2>
            <p className="text-sm text-gray-500">Ask about nutrition, workouts, or how your day is going.</p>
          </Link>

          <div className="bg-white rounded-xl border border-gray-200 p-6 opacity-60 cursor-not-allowed">
            <h2 className="text-lg font-semibold text-gray-800 mb-1">Today&apos;s Log</h2>
            <p className="text-sm text-gray-500">Log meals, workouts, and how you feel.</p>
          </div>
        </div>
      </div>
    </main>
  );
}
