---
name: frontend-workflow
description: Workflow for adding new data fetching, components, and pages to the frontend
allowed-tools: Read, Write, Edit, Bash, Glob
---

## Frontend Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS v4
- **Forms**: react-hook-form + zod
- **Data fetching**: `apiClient` from `@/lib/api-client` (typed fetch wrapper over Next.js API routes)
- **State**: React local state (`useState`, `useReducer`) — no global state library
- **UI primitives**: `src/components/ui/` (shadcn-style, hand-rolled)

---

## Project Structure

```
src/
  app/
    (private)/          # Auth-protected routes
    (public)/           # Public routes (login, signup, etc.)
    api/                # Next.js Route Handlers (backend)
  modules/              # Feature modules
    <feature>/
      components/       # UI components
      hooks/            # Custom hooks
      types/index.ts    # TypeScript types
      index.ts          # Barrel export
      README.md         # Module documentation (auto-generated)
      tests/            # Playwright tests (auto-generated)
  components/
    ui/                 # Shared UI primitives (Button, Input, Card, etc.)
    customs/            # Shared custom components
  lib/
    utils.ts            # cn() helper
    api-client.ts       # Typed fetch wrapper
```

---

## Adding a New Data Fetch

Never call `fetch` directly from a component. Always:

1. Define the API route in `src/app/api/<feature>/route.ts`
2. Create a hook in `src/modules/<feature>/hooks/use<Feature>.ts`

```typescript
// src/modules/users/hooks/useUsers.ts
import { useState, useEffect } from "react";
import { apiClient, ApiError } from "@/lib/api-client";
import type { User } from "../types";

export function useUsers() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient
      .get<User[]>("/api/users")
      .then(setUsers)
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Failed to load");
      })
      .finally(() => setIsLoading(false));
  }, []);

  return { users, isLoading, error };
}
```

---

## Component Conventions

- **Shared across app** → `src/components/`
- **Feature-specific** → `src/modules/<feature>/components/`
- **UI primitives** → `src/components/ui/` (Button, Input, Card, Label, etc.)
- Always handle loading and error states
- Use `cn()` from `@/lib/utils` for conditional classes
- Use `lucide-react` for icons

### Standard Component Template

```tsx
"use client"; // only if using hooks/events

import { cn } from "@/lib/utils";

interface MyComponentProps {
  title: string;
  className?: string;
  children?: React.ReactNode;
}

export function MyComponent({ title, className, children }: MyComponentProps) {
  return (
    <div className={cn("base-classes", className)}>
      <h2>{title}</h2>
      {children}
    </div>
  );
}
```

---

## API Route Template

```typescript
// src/app/api/<feature>/route.ts
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

const schema = z.object({
  /* ... */
});

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const parsed = schema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json({ message: "Invalid input" }, { status: 400 });
    }

    // business logic here

    return NextResponse.json(
      {
        /* response */
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
```

---

## Key Rules

- No `any` types — type all props and return values
- No direct `fetch` in components — use `apiClient`
- Export everything from `index.ts`
- Use `@/` path aliases — no relative `../../` imports
- Every new module gets a `README.md` and Playwright tests (see `/new-module` command)
