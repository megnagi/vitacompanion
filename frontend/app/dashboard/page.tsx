"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSession, signOut } from "next-auth/react";

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [firstName, setFirstName] = useState("");

  useEffect(() => {
    if (status === "loading") return;

    if (status === "authenticated") {
      fetch("/api/auth/sync", { method: "POST" })
        .then(async (r) => {
          if (r.status === 404) {
            router.replace("/onboarding");
            return null;
          }
          return r.ok ? r.json() : null;
        })
        .then((d) => {
          if (!d) return;
          // User row exists but health profile was never created — needs onboarding
          if (d.has_profile === false) {
            router.replace("/onboarding");
            return;
          }
          const name = d.full_name ?? session?.user?.name ?? "";
          setFirstName(name.split(" ")[0]);
        })
        .catch(() => {
          setFirstName(session?.user?.name?.split(" ")[0] ?? "");
        });
    } else {
      setFirstName("Test");
    }
  }, [status, session, router]);

  const today = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <main className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <span className="text-xl font-bold text-gray-900">VitaCompanion</span>
        <button
          onClick={() => signOut({ callbackUrl: "/" })}
          className="text-sm text-gray-500 hover:text-gray-800"
        >
          Sign out
        </button>
      </nav>

      <div className="max-w-2xl mx-auto px-6 py-12 flex flex-col gap-6">
        <div>
          <p className="text-sm text-gray-500">{today}</p>
          <h1 className="text-3xl font-bold text-gray-900 mt-1">
            {firstName ? `Welcome back, ${firstName}!` : "Welcome back!"}
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

          <Link
            href="/log"
            className="block bg-white rounded-xl border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            <h2 className="text-lg font-semibold text-gray-800 mb-1">Today&apos;s Log</h2>
            <p className="text-sm text-gray-500">Log meals, workouts, and how you feel.</p>
          </Link>
        </div>
      </div>
    </main>
  );
}
