---
description: Create a new page or route in the application
allowed-tools: Read, Write, Edit, Glob
---

Create a new page for: $ARGUMENTS

<!--
  CUSTOMIZE THIS FILE:
  Update the file paths and steps to match your routing framework.
  Examples: Next.js App Router, React Router, Django URLs, Rails routes, etc.
-->

Steps:

1. Create the page file at the correct path for your routing framework
   - Next.js App Router: `src/app/<route>/page.tsx`
   - React Router: `src/pages/<RouteName>.tsx`
   - Django: `<app>/views.py` + register in `urls.py`
2. If the page needs data, create or reference the appropriate module under `src/modules/<route>/`
3. Register the route in the app's navigation or router config
4. Apply consistent layout, loading states, and error boundaries following existing page patterns

The page should follow the same structure as existing pages in the codebase.
