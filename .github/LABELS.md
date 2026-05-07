# PR Labels

Three labels control all Claude automation. **Nothing runs automatically** — every action requires a label to be applied.

| Label            | What happens                                                                                         |
| ---------------- | ---------------------------------------------------------------------------------------------------- |
| `review:pr`      | Claude reviews the PR diff and posts a comment with findings                                         |
| `generate:tests` | Claude writes Playwright tests → new branch `claude-{your-branch}` → new PR → comment on original PR |
| `generate:docs`  | Claude writes module README → new branch `claude-{your-branch}` → new PR → comment on original PR    |

Issues with `@claude` in the body trigger the issue workflow automatically (unchanged).

---

## Branch and PR flow for generate:tests / generate:docs

```
your-branch  ──(label added)──▶  claude-your-branch
                                       │
                                       ▼
                                  PR opened:
                                  claude-your-branch → your-branch
                                       │
                                       ▼
                                  Comment posted on original PR
                                  with link to the new PR
```

If both labels are applied, both workflows reuse the same `claude-{branch}` branch and the second workflow updates the existing PR body rather than opening a duplicate.

---

## Create labels (run once)

```bash
gh label create "review:pr"       --color "d93f0b" --description "Trigger Claude PR review"
gh label create "generate:tests"  --color "0075ca" --description "Generate Playwright tests for changed modules"
gh label create "generate:docs"   --color "e4e669" --description "Generate module documentation"
```

## Required secret

`ANTHROPIC_API_KEY` → Settings → Secrets and variables → Actions

## Cost controls

- Model: `claude-haiku-4-5` on all workflows
- `--max-turns 5` on generate, `--max-turns 3` on review
- `fetch-depth: 1` everywhere
- Claude is told to read only the specific files it needs
- Zero automatic triggers on PR open/push/sync
