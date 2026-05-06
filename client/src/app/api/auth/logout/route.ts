import { NextResponse } from "next/server";

/**
 * POST /api/auth/logout
 * Client clears localStorage; this route exists for consistency.
 */
export async function POST() {
  return NextResponse.json({ success: true }, { status: 200 });
}
