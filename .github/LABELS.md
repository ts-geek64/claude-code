# PR Labels Setup

Two labels must exist in the GitHub repository for the automation workflows to trigger.
Create them once under **Settings → Labels**.

| Label            | Color     | Description                                                          |
| ---------------- | --------- | -------------------------------------------------------------------- |
| `generate:tests` | `#0075ca` | Triggers Claude to write/update Playwright tests for changed modules |
| `generate:docs`  | `#e4e669` | Triggers Claude to write/update README.md for changed modules        |

## How to create labels via GitHub CLI

```bash
gh label create "generate:tests" --color "0075ca" --description "Generate Playwright tests for changed modules"
gh label create "generate:docs"  --color "e4e669" --description "Generate module documentation"
```

## How it works

1. Open a PR that adds or modifies files inside `client/src/modules/<name>/`
2. Add the label `generate:tests` and/or `generate:docs`
3. The corresponding workflow triggers automatically
4. Claude reads all source files in the changed module(s), then writes or replaces:
   - `client/src/modules/<name>/tests/<name>.spec.ts`
   - `client/src/modules/<name>/README.md`
5. Changes are committed directly to the PR branch
6. A comment is posted on the PR with links to the updated files

## Required secret

Add `ANTHROPIC_API_KEY` to **Settings → Secrets and variables → Actions**.
