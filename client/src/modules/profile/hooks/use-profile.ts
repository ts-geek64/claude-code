"use client";

import { useState, useEffect } from "react";
import { apiClient, ApiError } from "@/lib/api-client";
import type {
  Profile,
  UpdateProfilePayload,
  UpdateProfileResponse,
} from "../types";

interface UseProfileReturn {
  profile: Profile | null;
  isLoading: boolean;
  error: string | null;
  updateName: (payload: UpdateProfilePayload) => Promise<void>;
  isUpdating: boolean;
  updateError: string | null;
  updateSuccess: boolean;
}

export function useProfile(userId: string | null): UseProfileReturn {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [isUpdating, setIsUpdating] = useState(false);
  const [updateError, setUpdateError] = useState<string | null>(null);
  const [updateSuccess, setUpdateSuccess] = useState(false);

  useEffect(() => {
    if (!userId) return;

    setIsLoading(true);
    setError(null);

    apiClient
      .get<{ profile: Profile }>(`/api/profile?id=${userId}`)
      .then((res) => setProfile(res.profile))
      .catch((err) => {
        setError(
          err instanceof ApiError ? err.message : "Failed to load profile",
        );
      })
      .finally(() => setIsLoading(false));
  }, [userId]);

  const updateName = async (payload: UpdateProfilePayload) => {
    if (!profile) return;

    setIsUpdating(true);
    setUpdateError(null);
    setUpdateSuccess(false);

    try {
      const res = await apiClient.patch<UpdateProfileResponse>("/api/profile", {
        id: profile.id,
        ...payload,
      });
      setProfile(res.profile);
      setUpdateSuccess(true);
    } catch (err) {
      setUpdateError(
        err instanceof ApiError ? err.message : "Failed to update profile",
      );
    } finally {
      setIsUpdating(false);
    }
  };

  return {
    profile,
    isLoading,
    error,
    updateName,
    isUpdating,
    updateError,
    updateSuccess,
  };
}
