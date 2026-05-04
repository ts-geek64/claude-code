---
description: Review frontend code for quality, patterns, and consistency
allowed-tools: Read, Glob, Bash
---

Review frontend code: $ARGUMENTS

<!--
  CUSTOMIZE THIS FILE:
  Add or remove checklist items based on your frontend stack.
-->

Check for:

**Data Fetching**

1. Is the correct API client / data fetching pattern being used?
2. Are loading and error states handled?
3. Is data properly typed end-to-end?

**TypeScript** 4. No `any` types — proper typing of props and return values? 5. Are component props interfaces defined?

**Component Structure** 6. Is the component in the right place (shared vs feature-specific)? 7. Is it broken into appropriately sized sub-components? 8. Are side effects in the right place (useEffect, event handlers)?

**Styling** 9. Using the project's utility classes / design system consistently? 10. No inline styles unless absolutely necessary? 11. Responsive behavior considered?

**Accessibility** 12. Interactive elements have accessible labels? 13. Keyboard navigation works? 14. Color contrast is sufficient?

**Performance** 15. No unnecessary re-renders (missing memoization, unstable references)? 16. Large lists virtualized if needed?

Provide specific, actionable feedback with file and line references.
