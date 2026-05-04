---
name: architecture
description: Guide for implementing features following the project's layered architecture
allowed-tools: Read, Write, Edit, Glob
---

<!--
  CUSTOMIZE THIS FILE:
  Replace the content below with your actual project architecture.
  Describe your layers, patterns, and rules so Claude understands how your codebase is structured.
  The more specific you are, the better Claude will follow your conventions.
-->

## Project Architecture

### Overview

This project follows a **[YOUR ARCHITECTURE NAME]** pattern.  
Example: Clean Architecture / Layered Architecture / MVC / Feature-Sliced Design

### Layers (from outermost to innermost)

```
[Entry Point]  →  [Controller/Handler]  →  [Service]  →  [Repository]  →  [Database]
     ↑                    ↑                     ↑               ↑
  HTTP/CLI            Parse input           Business          Data
  Events              Validate              Logic             Access
```

### Layer Rules

**Entry Point** (`src/routes/` or `src/api/`)

- Only registers routes/handlers
- No business logic here

**Controller / Handler** (`src/controllers/`)

- Parses and validates incoming request
- Calls the appropriate service
- Returns the response
- No database access here

**Service** (`src/services/`)

- Contains all business logic
- Calls repositories for data
- Orchestrates multi-step operations using transactions
- No SQL or HTTP calls here

**Repository** (`src/repositories/`)

- All database queries live here
- Maps database rows to domain objects
- No business logic here

### Key Rules

- SQL only in repositories — never in services or controllers
- Services depend on interfaces, not concrete implementations
- Use the project's logger — never `console.log`
- Use typed custom errors — never raw `new Error("string")`
- All imports use path aliases — no long relative paths

### File Naming

- Files: `kebab-case.ts`
- Classes/Interfaces: `PascalCase`
- Functions/Variables: `camelCase`
- Constants: `UPPER_SNAKE_CASE`

### Adding a New Feature

See the `/new-feature` command for the step-by-step scaffold process.
