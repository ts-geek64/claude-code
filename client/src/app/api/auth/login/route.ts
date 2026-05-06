import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { findByEmail, makeToken } from "@/lib/user-store";

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const parsed = loginSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { message: "Invalid email or password format" },
        { status: 400 },
      );
    }

    const { email, password } = parsed.data;
    const user = findByEmail(email);

    if (!user || user.password !== password) {
      return NextResponse.json(
        { message: "Invalid email or password" },
        { status: 401 },
      );
    }

    return NextResponse.json(
      {
        token: makeToken(user),
        user: { id: user.id, email: user.email, name: user.name },
      },
      { status: 200 },
    );
  } catch {
    return NextResponse.json(
      { message: "Internal server error" },
      { status: 500 },
    );
  }
}
