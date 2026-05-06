"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, User, CheckCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useProfile } from "../hooks/use-profile";
import { useAuth } from "@/modules/auth";

const updateSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
});

type UpdateFormValues = z.infer<typeof updateSchema>;

export function ProfileCard() {
  const { user } = useAuth();
  const {
    profile,
    isLoading,
    error,
    updateName,
    isUpdating,
    updateError,
    updateSuccess,
  } = useProfile(user?.id ?? null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<UpdateFormValues>({
    resolver: zodResolver(updateSchema),
  });

  if (isLoading) {
    return (
      <Card className="w-full max-w-md">
        <CardContent className="flex items-center justify-center py-12">
          <Loader2
            className="h-6 w-6 animate-spin text-zinc-400"
            aria-label="Loading profile"
          />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="w-full max-w-md">
        <CardContent className="py-8">
          <p role="alert" className="text-sm text-red-600 dark:text-red-400">
            {error}
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <User className="h-4 w-4" aria-hidden="true" />
          Your profile
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Read-only email */}
        <div className="space-y-1.5">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            value={profile?.email ?? ""}
            readOnly
            disabled
            aria-label="Email address (read only)"
          />
        </div>

        {/* Editable name */}
        <form
          onSubmit={handleSubmit((values) => updateName(values))}
          noValidate
          aria-label="Update profile form"
        >
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="name">Display name</Label>
              <Input
                id="name"
                type="text"
                defaultValue={profile?.name ?? ""}
                placeholder="Your name"
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

            {updateError && (
              <p
                role="alert"
                className="text-sm text-red-600 dark:text-red-400"
              >
                {updateError}
              </p>
            )}

            {updateSuccess && (
              <p
                role="status"
                className="flex items-center gap-1.5 text-sm text-green-600 dark:text-green-400"
              >
                <CheckCircle className="h-4 w-4" aria-hidden="true" />
                Profile updated
              </p>
            )}

            <Button type="submit" disabled={isUpdating} aria-busy={isUpdating}>
              {isUpdating ? (
                <>
                  <Loader2
                    className="h-4 w-4 animate-spin"
                    aria-hidden="true"
                  />
                  Saving…
                </>
              ) : (
                "Save changes"
              )}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
