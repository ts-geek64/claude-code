"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import type { AuthUser } from "../types";

const TOKEN_KEY = "auth_token";

function parseToken(token: string): AuthUser | null {
  try {
    return JSON.parse(atob(token)) as AuthUser;
  } catch {
    return null;
  }
}

interface UseAuthReturn {
  user: AuthUser | null;
  isAuthenticated: boolean;
  logout: () => void;
}

export function useAuth(): UseAuthReturn {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      setUser(parseToken(token));
    }
  }, []);

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
    router.push("/login");
  };

  return {
    user,
    isAuthenticated: user !== null,
    logout,
  };
}
