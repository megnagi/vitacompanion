import { getServerSession } from "next-auth";
import { NextResponse } from "next/server";
import { authOptions } from "../[...nextauth]/route";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * POST /api/auth/sync
 * Reads the current next-auth session and looks up the matching vita user.
 * Always calls the backend so has_profile is always fresh (never stale JWT cache).
 * Returns { user_id, full_name, email, persona, has_profile } or 401/404.
 */
export async function POST() {
  const session = await getServerSession(authOptions);

  if (!session?.user?.email) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 });
  }

  try {
    const res = await fetch(
      `${API_URL}/users/by-email/${encodeURIComponent(session.user.email)}`
    );
    if (res.ok) {
      const data = await res.json();
      return NextResponse.json(data); // includes has_profile
    }
    if (res.status === 404) {
      return NextResponse.json(
        { error: "User not found — onboarding required" },
        { status: 404 }
      );
    }
    return NextResponse.json({ error: "Backend error" }, { status: 502 });
  } catch {
    return NextResponse.json({ error: "Backend unreachable" }, { status: 502 });
  }
}
