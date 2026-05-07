"use client";

import Link from "next/link";
import { useAuth } from "@/modules/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LogOut, User } from "lucide-react";

export default function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      {/* Top nav */}
      <header className="border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
          <span className="font-semibold text-zinc-900 dark:text-zinc-50">
            Dashboard
          </span>
          <Button variant="ghost" size="sm" onClick={logout} className="gap-2">
            <LogOut className="h-4 w-4" aria-hidden="true" />
            Sign out
          </Button>
        </div>
      </header>

      {/* Content */}
      <main className="mx-auto max-w-5xl px-4 py-10">
        <h1 className="mb-6 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
          Welcome back{user?.name ? `, ${user.name}` : ""}
        </h1>

        <Card className="max-w-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <User className="h-4 w-4" aria-hidden="true" />
              Your account
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-zinc-600 dark:text-zinc-400">
            <div className="flex justify-between">
              <span className="font-medium text-zinc-900 dark:text-zinc-50">
                Name
              </span>
              <span>{user?.name ?? "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium text-zinc-900 dark:text-zinc-50">
                Email
              </span>
              <span>{user?.email ?? "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium text-zinc-900 dark:text-zinc-50">
                ID
              </span>
              <span className="font-mono text-xs">{user?.id ?? "—"}</span>
            </div>
            <div className="pt-1">
              <Link
                href="/profile"
                className="text-xs font-medium text-zinc-900 underline-offset-4 hover:underline dark:text-zinc-50"
              >
                Edit profile →
              </Link>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
