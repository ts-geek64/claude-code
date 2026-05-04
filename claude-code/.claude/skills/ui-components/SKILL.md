---
name: ui-components
description: Conventions for building UI components in this project
allowed-tools: Read, Write, Edit, Glob
---

<!--
  CUSTOMIZE THIS FILE:
  Replace the content below with your actual UI component conventions.
  Include your component library, design tokens, and patterns.
-->

## UI Component Conventions

### Component Library

This project uses **[YOUR COMPONENT LIBRARY]**.  
Examples: shadcn/ui, Material UI, Ant Design, Chakra UI, custom design system

### Where to Put Components

| Type                        | Location                                          |
| --------------------------- | ------------------------------------------------- |
| Shared across the whole app | `src/components/`                                 |
| Specific to one feature     | `src/modules/<feature>/components/`               |
| Design system primitives    | `src/components/ui/` (managed by the library CLI) |

### Standard Component Template

```tsx
// [YOUR FRAMEWORK] component template
// Customize this for your stack

interface MyComponentProps {
  title: string;
  className?: string;
  children?: React.ReactNode;
}

export function MyComponent({ title, className, children }: MyComponentProps) {
  return (
    <div className={/* your className utility */}>
      <h2>{title}</h2>
      {children}
    </div>
  );
}
```

### Key Conventions

- Use the project's className utility for conditional classes (e.g. `cn()`, `clsx()`, `classnames()`)
- Use the project's icon library consistently (e.g. lucide-react, heroicons, FontAwesome)
- Loading states: use skeleton components or spinners from the design system
- Empty states: use a consistent empty state component
- Always export from the module's `index.ts`

### Available Shared Components

Check `src/components/index.ts` (or equivalent) for all available shared components before building new ones.
