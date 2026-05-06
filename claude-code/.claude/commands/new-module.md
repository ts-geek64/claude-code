---
description: Scaffold a new feature module with all required files, documentation, and Playwright tests
allowed-tools: Read, Write, Edit, Bash, Glob
---

Create a new feature module: $ARGUMENTS

## Directory Structure

Scaffold under `src/modules/<module-name>/`:

```
src/modules/<module-name>/
  components/         # UI components for this feature
  hooks/              # Custom hooks (data fetching, state)
  types/index.ts      # TypeScript interfaces
  index.ts            # Barrel export
```

API route (if the module needs backend logic):

```
src/app/api/<module-name>/route.ts
```

Page route:

```
src/app/(private)/<module-name>/page.tsx   # auth-protected
src/app/(public)/<module-name>/page.tsx    # public
```

---

## Steps

### 1 — Scaffold the module

1. Read an existing module in `src/modules/` as a reference (e.g. `src/modules/auth/`)
2. Create `src/modules/<module-name>/types/index.ts` with the main data interfaces
3. Create `src/modules/<module-name>/hooks/use<ModuleName>.ts` — data fetching hook using `apiClient` from `@/lib/api-client`
4. Create `src/modules/<module-name>/components/<ModuleName>Form.tsx` (or relevant component)
   - Use primitives from `src/components/ui/`
   - Use `react-hook-form` + `zod` for any forms
   - Handle loading and error states
5. Create `src/modules/<module-name>/index.ts` barrel export
6. Create the API route at `src/app/api/<module-name>/route.ts` using Next.js Route Handlers
7. Create the page at the correct route group path

### 2 — Generate documentation

After scaffolding, create `src/modules/<module-name>/README.md` with this structure:

```markdown
# <ModuleName> Module

## Overview

Brief description of what this module does.

## File Structure

List each file and its responsibility.

## API Routes

| Method | Path | Description | Request Body | Response |
| ------ | ---- | ----------- | ------------ | -------- |

## Components

Document each component: props, usage example.

## Hooks

Document each hook: parameters, return values, usage example.

## Types

List all exported types/interfaces.

## Usage Example

A complete code example showing how to use this module in a page.
```

### 3 — Generate Playwright tests

Create `src/modules/<module-name>/tests/<module-name>.spec.ts` with:

```typescript
import { test, expect } from "@playwright/test";

// Cover these scenarios:
// 1. Happy path — successful interaction
// 2. Validation errors — empty/invalid form fields
// 3. API error — server returns error response
// 4. Loading state — button shows spinner while submitting
// 5. Accessibility — form labels, aria attributes, keyboard nav
```

Use `page.getByRole()` and `page.getByLabel()` selectors (never CSS selectors).
Mock API routes using `page.route()` to avoid real network calls.

---

## Conventions

- Never call `fetch` directly from components — always use `apiClient` from `@/lib/api-client`
- No `any` types — all props and return values must be typed
- Export everything from `index.ts`
- Use `cn()` from `@/lib/utils` for conditional classNames
- Use primitives from `src/components/ui/` — do not install new UI libraries
- File naming: `kebab-case` for files, `PascalCase` for components, `camelCase` for hooks
