---
description: Create a new database migration following the project's conventions
allowed-tools: Read, Write, Bash, Glob
---

Create a new migration for: $ARGUMENTS

<!--
  CUSTOMIZE THIS FILE:
  Replace the SQL template with your database/ORM conventions.
  Examples: Prisma schema, Alembic, Flyway, Rails ActiveRecord, Knex, etc.
  Update the "After Creating" command to match your migration runner.
-->

## Steps

1. Find the next sequential migration number in `migrations/`
2. Create `migrations/<N>-<kebab-case-description>.sql` (or the format your ORM uses)
3. Write the migration following the structure below

## Migration Template

```sql
-- Migration: [description]
-- Created: [date]

-- UP
CREATE TABLE IF NOT EXISTS your_table (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_your_table_name ON your_table (name);

-- DOWN (rollback)
-- DROP TABLE IF EXISTS your_table;
```

## Naming Conventions

- Tables: `snake_case`, plural (e.g. `user_profiles`)
- Indexes: `idx_<table>_<column>`
- Foreign keys: `fk_<table>_<referenced_table>`
- Unique constraints: `uk_<table>_<column>`

## After Creating

Run: `[YOUR MIGRATION COMMAND]`

<!-- Examples: npm run db:migrate | python manage.py migrate | rails db:migrate | npx prisma migrate dev -->
