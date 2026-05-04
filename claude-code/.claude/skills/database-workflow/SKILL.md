---
name: database-workflow
description: Workflow for creating and applying database migrations
allowed-tools: Read, Write, Bash, Glob
---

<!--
  CUSTOMIZE THIS FILE:
  Replace the content below with your actual database migration workflow.
  Include your ORM/migration tool, naming conventions, and any project-specific rules.
-->

## Database Migration Workflow

### Tools Used

- **ORM / Migration tool**: [e.g. Prisma, Alembic, Flyway, Knex, ActiveRecord, graphile-migrate]
- **Database**: [e.g. PostgreSQL, MySQL, SQLite]
- **Run migrations**: `[YOUR COMMAND]` — e.g. `npm run db:migrate` or `python manage.py migrate`

### Step 1 — Create the migration file

```bash
# Example commands (use whichever applies):
npx prisma migrate dev --name add_user_profiles
python manage.py makemigrations
rails generate migration AddUserProfiles
```

Or create manually: `migrations/<N>-<description>.sql`

### Step 2 — Write the migration

Follow these rules:

- Always use `IF NOT EXISTS` / `IF EXISTS` for idempotency
- Include both UP and DOWN (rollback) logic
- Add indexes for any column used in WHERE clauses or JOINs
- Add `created_at` and `updated_at` timestamps to every table

### Step 3 — Apply

```bash
[YOUR MIGRATION COMMAND]
```

### Step 4 — Verify

Check that the schema looks correct:

```bash
[YOUR SCHEMA INSPECT COMMAND]
# e.g. npx prisma studio | psql -c '\d table_name' | rails db:schema:dump
```

### Naming Conventions

| Object             | Convention           | Example           |
| ------------------ | -------------------- | ----------------- |
| Tables             | `snake_case`, plural | `user_profiles`   |
| Columns            | `snake_case`         | `first_name`      |
| Indexes            | `idx_<table>_<col>`  | `idx_users_email` |
| Foreign keys       | `fk_<table>_<ref>`   | `fk_orders_user`  |
| Unique constraints | `uk_<table>_<col>`   | `uk_users_email`  |

### Rules

- Never drop or rename a column in production without a deprecation period
- Never delete data in a migration — archive it instead
- Test rollback before merging
