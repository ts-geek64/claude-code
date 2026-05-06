# Auth Module

Handles user authentication: login, signup, session storage, and logout.

## Files

| File                         | Purpose                                                     |
| ---------------------------- | ----------------------------------------------------------- |
| `components/login-form.tsx`  | Email + password form, submits to `/api/auth/login`         |
| `components/signup-form.tsx` | Name + email + password form, submits to `/api/auth/signup` |
| `hooks/use-login.ts`         | Calls login API, stores token, redirects to `/dashboard`    |
| `hooks/use-signup.ts`        | Calls signup API, stores token, redirects to `/dashboard`   |
| `hooks/use-auth.ts`          | Reads current user from localStorage, exposes `logout()`    |
| `types/index.ts`             | All auth-related TypeScript types                           |

## API Routes

| Method | Path               | Body                                                | Response                            |
| ------ | ------------------ | --------------------------------------------------- | ----------------------------------- |
| POST   | `/api/auth/login`  | `{ email: string, password: string }`               | `{ token: string, user: AuthUser }` |
| POST   | `/api/auth/signup` | `{ name: string, email: string, password: string }` | `{ token: string, user: AuthUser }` |
| POST   | `/api/auth/logout` | —                                                   | `{ success: true }`                 |

Error responses: `400` invalid input, `401` wrong credentials, `409` email already exists, `500` server error.

## Components

### `LoginForm`

Login card with email/password fields, inline validation, forgot-password link, and a link to signup.

```tsx
import { LoginForm } from "@/modules/auth";

export default function LoginPage() {
  return <LoginForm />;
}
```

### `SignupForm`

Signup card with name, email, password, confirm-password fields, and a link to login.

```tsx
import { SignupForm } from "@/modules/auth";

export default function SignupPage() {
  return <SignupForm />;
}
```

## Hooks

### `useLogin()`

```ts
const { login, isLoading, error } = useLogin();
await login({ email: "user@example.com", password: "password123" });
// → stores token in localStorage, redirects to /dashboard
```

### `useSignup()`

```ts
const { signup, isLoading, error } = useSignup();
await signup({
  name: "Jane",
  email: "jane@example.com",
  password: "password123",
  confirmPassword: "password123",
});
// → stores token in localStorage, redirects to /dashboard
```

### `useAuth()`

```ts
const { user, isAuthenticated, logout } = useAuth();
// user: AuthUser | null — decoded from localStorage token
// logout() → clears token, redirects to /login
```

## Types

```ts
interface AuthUser {
  id: string;
  email: string;
  name: string;
}

interface LoginCredentials {
  email: string;
  password: string;
}

interface SignupCredentials {
  name: string;
  email: string;
  password: string;
  confirmPassword: string; // validated client-side only, not sent to API
}

interface AuthResponse {
  token: string;
  user: AuthUser;
}
```

## Usage

```tsx
// Protected page — read current user
"use client";
import { useAuth } from "@/modules/auth";

export default function Dashboard() {
  const { user, logout } = useAuth();
  return (
    <div>
      <p>Hello, {user?.name}</p>
      <button onClick={logout}>Sign out</button>
    </div>
  );
}
```

## Notes

- Token is a base64-encoded JSON object stored in `localStorage` under `auth_token`. Not a real JWT — demo only.
- User store is in-memory (`client/src/lib/user-store.ts`). Data resets on server restart.
- Pre-seeded accounts: `admin@test.com`, `user@test.com`, `demo@example.com` — all with password `password123`.
- The `(private)/layout.tsx` guards all routes under `(private)/` by checking for the token on mount.
