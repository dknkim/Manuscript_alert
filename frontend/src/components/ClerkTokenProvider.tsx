"use client";

/**
 * Invisible component — runs inside <ClerkProvider>, registers the Clerk
 * token getter with the API client so every fetch/SSE request includes
 * an Authorization: Bearer <token> header automatically.
 */

import { useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { initClerkTokenGetter } from "@/lib/api";

export function ClerkTokenProvider() {
  const { getToken, isLoaded } = useAuth();

  useEffect(() => {
    if (isLoaded) {
      initClerkTokenGetter(() => getToken());
    }
  }, [isLoaded, getToken]);

  return null;
}
