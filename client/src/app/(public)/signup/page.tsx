import type { Metadata } from "next";
import { SignupForm } from "@/modules/auth";

export const metadata: Metadata = {
  title: "Create account",
  description: "Create a new account",
};

export default function SignupPage() {
  return <SignupForm />;
}
