---
description: Review backend code for quality, architecture, and security
allowed-tools: Read, Glob, Bash
---

Review backend code: $ARGUMENTS

<!--
  CUSTOMIZE THIS FILE:
  Add or remove checklist items based on your stack and standards.
-->

Check against the project's standards:

**Architecture**

1. Is data access logic only in repositories/models? (not in controllers/services)
2. Is business logic only in services? (controllers should only parse input and delegate)
3. Are interfaces/abstractions used instead of concrete implementations where appropriate?
4. Are transactions used correctly for multi-step writes?

**Code Quality** 5. No `any` types — using proper interfaces or `unknown`? 6. All imports using the project's path aliases (no long relative paths like `../../../`)? 7. Files and variables named consistently with the rest of the codebase? 8. No dead code or commented-out blocks?

**Logging & Errors** 9. Using the project's logger (not `console.log`)? 10. Using typed/custom error classes instead of raw `new Error()`? 11. Errors are caught and handled — no unhandled promise rejections?

**Security** 12. No hardcoded secrets — using environment variables? 13. User input is validated before use? 14. Authentication/authorization checked before data access?

**Tests** 15. Are there tests for the new logic? 16. Edge cases covered (empty input, not found, unauthorized)?

Provide specific, actionable feedback with file and line references.
