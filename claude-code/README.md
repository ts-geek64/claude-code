# Claude Code

A ready-to-use setup for integrating Claude Code into any software project.  
Clone this, customize the placeholders, and drop it into your repo.

---

## What's Included

```
claude-code/
├── .claude/
│   ├── settings.json              # Hooks: auto-lint, block generated files, notifications
│   └── commands/                  # Slash commands you can run in Claude Code
│       ├── new-feature.md         # Scaffold a full feature (backend + frontend)
│       ├── new-module.md          # Scaffold a frontend module
│       ├── new-page.md            # Create a new page/route
│       ├── new-migration.md       # Create a database migration
│       ├── new-repository.md      # Add a data repository layer
│       ├── review-backend.md      # Code review for backend files
│       ├── review-frontend.md     # Code review for frontend files
│       └── debug.md               # Debug a specific issue
│   └── skills/                    # Reusable knowledge guides for Claude
│       ├── architecture/          # Your project's architecture patterns
│       ├── database-workflow/     # Database migration workflow
│       ├── frontend-workflow/     # Frontend component/data workflow
│       └── ui-components/         # UI component conventions
└── .github/
    └── workflows/
        ├── claude.yml             # @claude mention handler (issues, PRs, comments)
        └── claude-code-review.yml # Automatic PR code review
```

---

## Quick Setup

### 1. Copy files into your repo

```bash
cp -r claude-code/.claude   your-repo/.claude
cp -r claude-code/.github   your-repo/.github
```

### 2. Add your API key to GitHub Secrets

Go to your repo → **Settings → Secrets and variables → Actions** → New secret:

- Name: `ANTHROPIC_API_KEY`
- Value: your key from [console.anthropic.com](https://console.anthropic.com)

### 3. Customize for your project

Open each file and replace the `[PLACEHOLDER]` values with your project's specifics.  
See the **Customization Guide** section below.

---

## How to Use

### @claude mentions (GitHub Issues & PRs)

Mention `@claude` anywhere in an issue or PR comment:

```
@claude add a login page with email/password form
@claude fix the bug in the auth middleware
@claude review this PR and suggest improvements
```

Claude will create a branch, do the work, and open a PR automatically.

### Slash commands (Claude Code CLI / IDE)

```
/new-feature user profile settings
/new-migration add_user_preferences_table
/review-backend src/services/auth.ts
/debug why is the login form not submitting
```

---

## Customization Guide

### settings.json

| What to change                                           | Where                                  |
| -------------------------------------------------------- | -------------------------------------- |
| File extensions to lint (`.ts`, `.py`, `.go`, etc.)      | `PostToolUse` hook, `grep -qE` pattern |
| Lint command (`eslint`, `flake8`, `golangci-lint`, etc.) | `PostToolUse` hook, `command` field    |
| Generated/protected folders to block edits on            | `PreToolUse` hook, `grep -qE` pattern  |
| Session start reminders (package manager, conventions)   | `SessionStart` hook, `echo` message    |

### commands/

Each command file is a markdown prompt. Customize:

- The steps to match your project structure
- File paths and naming conventions
- Tech stack references (swap Next.js → Django, Apollo → REST, etc.)

### skills/

Skills are reference guides Claude loads when working on related tasks.  
Update them to describe your actual architecture, patterns, and conventions.

### GitHub Workflows

| File                     | What to customize                                      |
| ------------------------ | ------------------------------------------------------ |
| `claude.yml`             | `allowed_tools` — which bash commands Claude can run   |
| `claude.yml`             | `custom_instructions` — your project context and rules |
| `claude-code-review.yml` | `direct_prompt` — what to check during code review     |

---

## Requirements

- An [Anthropic API key](https://console.anthropic.com)
- GitHub repository with Actions enabled
- Claude Code CLI (for local slash commands): `npm install -g @anthropic-ai/claude-code`
