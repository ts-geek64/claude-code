# Auth Module

## Overview

Handles user authentication — login form, credential submission, and token storage.
Uses a Next.js API route as the backend endpoint.

## File Structure

```
src/modules/auth/
  components/
    LoginForm.tsx       # Login form with email/password fields and validation
  hooks/
    useLogin.ts         # Submits credentials, stores token, redirects on success
  types/
    index.ts            # LoginCredentials, LoginResponse, AuthUser interfaces
  index.ts              # Barrel export
  README.md             # This file
  tests/
    login.spec.ts       # Playwright end-to-end tests

src/app/
  (public)/login/
    page.tsx            # /login route — renders LoginForm
  api/auth/login/
    route.ts            # POST /api/auth/login — validates credentials, returns token
```

## API Routes

| Method | Path              | Description       | Request Body                          | Response                                       |
| ------ | ----------------- | ----------------- | ------------------------------------- | ---------------------------------------------- |
| `POST` | `/api/auth/login` | Authenticate user | `{ email: string, password: string }` | `{ token: string, user: { id, email, name } }` |

**Error responses:**

| Status | Condition               |
| ------ | ----------------------- |
| `400`  | Invalid input format    |
| `401`  | Wrong email or password |
| `500`  | Internal server error   |

## Components

### `LoginForm`

Renders the login card with email/password fields, inline validation errors, and a submit button.

**Props:** none

**Usage:**

```tsx
import { LoginForm } from "@/modules/auth";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center">
      <LoginForm />
    </main>
  );
}
```

## Hooks

### `useLogin()`

Submits login credentials to `/api/auth/login`, stores the returned token in `localStorage`, and redirects to `/dashboard` on success.

**Returns:**

```typescript
{
  login: (credentials: LoginCredentials) => Promise<void>;
  isLoading: boolean; // true while request is in-flight
  error: string | null; // server-side error message
}
```

**Usage:**

```tsx
const { login, isLoading, error } = useLogin();

await login({ email: "user@example.com", password: "secret123" });
```

## Types

```typescript
interface LoginCredentials {
  email: string;
  password: string;
}

interface LoginResponse {
  token: string;
  user: { id: string; email: string; name: string };
}

interface AuthUser {
  id: string;
  email: string;
  name: string;
}
```

## Usage Example

```tsx
// src/app/(public)/login/page.tsx
import { LoginForm } from "@/modules/auth";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-50">
      <LoginForm />
    </main>
  );
}
```

## Notes

- The API route currently uses a stub validator. Replace the `isValidUser` check with real DB + bcrypt logic.
- The token is stored in `localStorage` for simplicity. For production, use an `httpOnly` cookie via `Set-Cookie` header.
- To add a logout flow, clear `localStorage` and redirect to `/login`.
