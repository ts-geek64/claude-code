"use client";

import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useSignup } from "../hooks/use-signup";

const signupSchema = z
  .object({
    name: z.string().min(2, "Name must be at least 2 characters"),
    email: z.string().email("Please enter a valid email address"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type SignupFormValues = z.infer<typeof signupSchema>;

export function SignupForm() {
  const { signup, isLoading, error } = useSignup();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupFormValues>({
    resolver: zodResolver(signupSchema),
  });

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="space-y-1">
        <CardTitle>Create an account</CardTitle>
        <CardDescription>Enter your details to get started</CardDescription>
      </CardHeader>

      <CardContent>
        <form
          onSubmit={handleSubmit(signup)}
          noValidate
          aria-label="Sign up form"
        >
          <div className="space-y-4">
            {error && (
              <div
                role="alert"
                className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-400"
              >
                {error}
              </div>
            )}

            {/* Name */}
            <div className="space-y-1.5">
              <Label htmlFor="name">Full name</Label>
              <Input
                id="name"
                type="text"
                placeholder="Jane Smith"
                autoComplete="name"
                aria-describedby={errors.name ? "name-error" : undefined}
                aria-invalid={!!errors.name}
                {...register("name")}
              />
              {errors.name && (
                <p
                  id="name-error"
                  role="alert"
                  className="text-xs text-red-600 dark:text-red-400"
                >
                  {errors.name.message}
                </p>
              )}
            </div>

            {/* Email */}
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                autoComplete="email"
                aria-describedby={errors.email ? "email-error" : undefined}
                aria-invalid={!!errors.email}
                {...register("email")}
              />
              {errors.email && (
                <p
                  id="email-error"
                  role="alert"
                  className="text-xs text-red-600 dark:text-red-400"
                >
                  {errors.email.message}
                </p>
              )}
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                autoComplete="new-password"
                aria-describedby={
                  errors.password ? "password-error" : undefined
                }
                aria-invalid={!!errors.password}
                {...register("password")}
              />
              {errors.password && (
                <p
                  id="password-error"
                  role="alert"
                  className="text-xs text-red-600 dark:text-red-400"
                >
                  {errors.password.message}
                </p>
              )}
            </div>

            {/* Confirm password */}
            <div className="space-y-1.5">
              <Label htmlFor="confirmPassword">Confirm password</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="••••••••"
                autoComplete="new-password"
                aria-describedby={
                  errors.confirmPassword ? "confirm-error" : undefined
                }
                aria-invalid={!!errors.confirmPassword}
                {...register("confirmPassword")}
              />
              {errors.confirmPassword && (
                <p
                  id="confirm-error"
                  role="alert"
                  className="text-xs text-red-600 dark:text-red-400"
                >
                  {errors.confirmPassword.message}
                </p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={isLoading}
              aria-busy={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2
                    className="h-4 w-4 animate-spin"
                    aria-hidden="true"
                  />
                  Creating account…
                </>
              ) : (
                "Create account"
              )}
            </Button>
          </div>
        </form>
      </CardContent>

      <CardFooter className="justify-center">
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Already have an account?{" "}
          <Link
            href="/login"
            className="font-medium text-zinc-900 underline-offset-4 hover:underline dark:text-zinc-50"
          >
            Sign in
          </Link>
        </p>
      </CardFooter>
    </Card>
  );
}
