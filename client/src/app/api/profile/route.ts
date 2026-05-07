import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { findByEmail } from "@/lib/user-store";

const updateSchema = z.object({
  id: z.string(),
  name: z.string().min(2, "Name must be at least 2 characters"),
});

/** GET /api/profile?id=<userId> */
export async function GET(request: NextRequest) {
  const id = request.nextUrl.searchParams.get("id");

  if (!id) {
    return NextResponse.json({ message: "Missing user id" }, { status: 400 });
  }

  // In-memory store — find by id
  const { users } = await import("@/lib/user-store");
  const user = users.find((u) => u.id === id);

  if (!user) {
    return NextResponse.json({ message: "User not found" }, { status: 404 });
  }

  return NextResponse.json(
    { profile: { id: user.id, name: user.name, email: user.email } },
    { status: 200 },
  );
}

/** PATCH /api/profile — update display name */
export async function PATCH(request: NextRequest) {
  try {
    const body = await request.json();
    const parsed = updateSchema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json(
        { message: parsed.error.issues[0].message },
        { status: 400 },
      );
    }

    const { id, name } = parsed.data;
    const { users } = await import("@/lib/user-store");
    const user = users.find((u) => u.id === id);

    if (!user) {
      return NextResponse.json({ message: "User not found" }, { status: 404 });
    }

    user.name = name;

    return NextResponse.json(
      { profile: { id: user.id, name: user.name, email: user.email } },
      { status: 200 },
    );
  } catch {
    return NextResponse.json(
      { message: "Internal server error" },
      { status: 500 },
    );
  }
}
