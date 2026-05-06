import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { findByEmail, createUser, makeToken } from "@/lib/user-store";

const signupSchema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
  password: z.string().min(8),
});

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const parsed = signupSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json({ message: "Invalid input" }, { status: 400 });
    }

    const { name, email, password } = parsed.data;

    if (findByEmail(email)) {
      return NextResponse.json(
        { message: "An account with this email already exists" },
        { status: 409 },
      );
    }

    const user = createUser(email, password, name);

    return NextResponse.json(
      {
        token: makeToken(user),
        user: { id: user.id, email: user.email, name: user.name },
      },
      { status: 201 },
    );
  } catch {
    return NextResponse.json(
      { message: "Internal server error" },
      { status: 500 },
    );
  }
}
