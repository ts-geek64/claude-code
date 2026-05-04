---
description: Debug a specific issue or error in the codebase
allowed-tools: Read, Glob, Bash
---

Debug this issue: $ARGUMENTS

<!--
  CUSTOMIZE THIS FILE:
  Add project-specific debugging steps relevant to your stack.
-->

## Investigation Steps

1. **Reproduce** — identify the exact input/action that triggers the issue
2. **Locate** — find the relevant files using the error message, stack trace, or feature name
3. **Trace** — follow the code path from the entry point (API route, event handler, etc.) to where it fails
4. **Identify root cause** — is it a logic error, missing null check, wrong data type, config issue, or race condition?

## Common Causes to Check

- Missing null/undefined checks
- Incorrect async/await usage (missing await, unhandled promise)
- Wrong environment variable or config value
- Stale cache or out-of-sync generated files
- Type mismatch between what's sent and what's expected
- Missing error handling in a try/catch

## After Finding the Cause

1. Explain what the root cause is
2. Show the minimal fix
3. Note if there are similar patterns elsewhere in the codebase that might have the same issue
