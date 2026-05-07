import type { Metadata } from "next";
import { ProfileCard } from "@/modules/profile";

export const metadata: Metadata = {
  title: "Profile",
  description: "View and update your profile",
};

export default function ProfilePage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-50 px-4 dark:bg-zinc-950">
      <ProfileCard />
    </main>
  );
}
