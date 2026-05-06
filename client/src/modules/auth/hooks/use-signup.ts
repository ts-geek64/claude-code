"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient, ApiError } from "@/lib/api-client";
import type { AuthResponse, SignupCredentials } from "../types";

interface UseSignupReturn {
  signup: (credentials: SignupCredentials) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export function useSignup(): UseSignupReturn {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const signup = async ({
    confirmPassword: _,
    ...credentials
  }: SignupCredentials) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.post<AuthResponse>(
        "/api/auth/signup",
        credentials,
      );

      localStorage.setItem("auth_token", response.token);
      router.push("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return { signup, isLoading, error };
}
