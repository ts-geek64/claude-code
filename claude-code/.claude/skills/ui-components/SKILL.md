---
name: ui-components
description: Conventions for building UI components in this project
allowed-tools: Read, Write, Edit, Glob
---

## UI Component Library

This project uses **hand-rolled shadcn-style primitives** located in `src/components/ui/`.
Do NOT install shadcn/ui CLI or any additional component libraries.

### Available Primitives

| Component                                                                         | Path                     | Usage                                                                                                               |
| --------------------------------------------------------------------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| `Button`                                                                          | `@/components/ui/button` | All clickable actions. Variants: `default`, `outline`, `ghost`, `destructive`. Sizes: `default`, `sm`, `lg`, `icon` |
| `Input`                                                                           | `@/components/ui/input`  | All text inputs                                                                                                     |
| `Label`                                                                           | `@/components/ui/label`  | Form field labels — always pair with an `Input` via `htmlFor`                                                       |
| `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter` | `@/components/ui/card`   | Content containers                                                                                                  |

### Where to Put Components

| Type                        | Location                            |
| --------------------------- | ----------------------------------- |
| Shared across the whole app | `src/components/customs/`           |
| Design system primitives    | `src/components/ui/`                |
| Feature-specific            | `src/modules/<feature>/components/` |

### Adding a New Primitive

Copy the pattern from an existing primitive (e.g. `input.tsx`):

1. Use `React.forwardRef` for all primitives
2. Accept a `className` prop and merge with `cn()`
3. Export the component and its props interface
4. Add it to this skill file

### Standard Form Pattern

```tsx
"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const schema = z.object({
  email: z.string().email(),
});

type FormValues = z.infer<typeof schema>;

export function MyForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  return (
    <form onSubmit={handleSubmit(console.log)} noValidate>
      <Label htmlFor="email">Email</Label>
      <Input
        id="email"
        type="email"
        aria-invalid={!!errors.email}
        aria-describedby={errors.email ? "email-error" : undefined}
        {...register("email")}
      />
      {errors.email && (
        <p id="email-error" role="alert">
          {errors.email.message}
        </p>
      )}
      <Button type="submit">Submit</Button>
    </form>
  );
}
```

### Key Rules

- Use `cn()` from `@/lib/utils` for all conditional classNames
- Use `lucide-react` for icons — no other icon libraries
- Always pair `Label` with `Input` via `htmlFor`/`id`
- Always add `aria-invalid` and `aria-describedby` on inputs with validation errors
- Loading states: use `<Loader2 className="animate-spin" />` from lucide-react
