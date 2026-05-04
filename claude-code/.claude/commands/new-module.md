---
description: Scaffold a new feature module with all required files and structure
allowed-tools: Read, Write, Edit, Bash, Glob
---

Create a new feature module for: $ARGUMENTS

<!--
  CUSTOMIZE THIS FILE:
  Update the folder structure and steps to match your project's module conventions.
  Examples: Django apps, Rails engines, NestJS modules, Next.js feature folders, etc.
-->

Follow this structure under `src/modules/<module-name>/`:

```
src/modules/<module-name>/
  components/       # UI components for this feature
  hooks/            # Custom hooks or composables
  services/         # Business logic / API calls
  types/            # TypeScript types or interfaces
  index.ts          # Barrel export
```

Steps:

1. Create the directory structure above
2. Create a basic component with placeholder UI
3. Create a types file with the main data interface
4. Create a barrel `index.ts` exporting everything
5. Add any data fetching hooks following the project's standard pattern

Use an existing module in `src/modules/` as a reference for structure and patterns.
