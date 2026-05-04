---
name: frontend-workflow
description: Workflow for adding new data fetching, components, and pages to the frontend
allowed-tools: Read, Write, Edit, Bash, Glob
---

<!--
  CUSTOMIZE THIS FILE:
  Replace the content below with your actual frontend stack and patterns.
  Examples: React + REST, Vue + GraphQL, Next.js + tRPC, Angular + NgRx, etc.
-->

## Frontend Development Workflow

### Stack

- **Framework**: [e.g. Next.js, React, Vue, Angular]
- **Data fetching**: [e.g. React Query, Apollo Client, SWR, Axios, tRPC]
- **Styling**: [e.g. Tailwind CSS, CSS Modules, styled-components]
- **State management**: [e.g. Zustand, Redux, Pinia, Context API]
- **Forms**: [e.g. React Hook Form, Formik, VeeValidate]

### Adding a New Data Fetch

1. Define the API call in `src/services/<feature>.ts` (or your equivalent)
2. Create a custom hook in `src/hooks/use-<feature>.ts` that wraps the fetch
3. Use the hook in your component — never call the API directly from a component

```typescript
// src/hooks/use-users.ts
export function useUsers() {
  // [YOUR DATA FETCHING PATTERN]
  // e.g. return useQuery({ queryKey: ['users'], queryFn: fetchUsers })
}

// Component
const { data, isLoading, error } = useUsers();
```

### Component Conventions

- **Shared components** → `src/components/`
- **Feature-specific** → `src/modules/<feature>/components/`
- Always handle loading and error states
- Use the project's design system / component library

### Adding a New Page

1. Create the page file at the correct path
2. Create a module folder if the page needs its own data/components
3. Register the route in the router or navigation config

### Key Rules

- Never call APIs directly from components — use hooks
- Always type your props — no `any`
- Use the project's utility functions for classNames, formatting, etc.
- Export components from the module's `index.ts` barrel file
