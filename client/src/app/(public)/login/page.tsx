import type { Metadata } from "next";
import { LoginForm } from "@/modules/auth";

export const metadata: Metadata = {
  title: "Sign in",
  description: "Sign in to your account",
};

export default function LoginPage() {
  return <LoginForm />;
}
