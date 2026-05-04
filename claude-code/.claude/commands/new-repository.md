---
description: Add a new data repository or data access layer
allowed-tools: Read, Write, Edit, Glob
---

Add a new repository for: $ARGUMENTS

<!--
  CUSTOMIZE THIS FILE:
  Update the patterns to match your data access approach.
  Examples: Repository pattern, Active Record, Django ORM, SQLAlchemy, Prisma client, etc.
-->

## Steps

1. **Define the interface** — `src/domain/repositories/<name>-repository.ts`
   - List all methods with typed inputs and outputs
   - Keep it framework-agnostic (no DB-specific types in the interface)

2. **Implement the class** — `src/repositories/<name>-repository.ts`
   - Implement the interface
   - All database queries go here — never in services or controllers
   - Map database rows (snake_case) → domain objects (camelCase)

3. **Register** — wire it up in your dependency injection container or factory

4. **Verify** — run `[YOUR LINT/BUILD COMMAND]`

## Key Rules

- No raw SQL in services or controllers — only in repositories
- Services depend on the interface, not the concrete class
- Use proper types — no `any`
- Handle not-found cases explicitly (return `null` or throw a typed error)

Reference existing repositories in `src/repositories/` for patterns.
