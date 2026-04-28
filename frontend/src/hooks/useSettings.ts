import { useState, useEffect, useCallback, useRef } from "react";
import { getClientCacheScope, getSettings, isAuthConfigured } from "@/lib/api";
import type { Settings } from "@/types";

const SETTINGS_TIMEOUT_MS = 8000;
const SETTINGS_RETRY_DELAYS_MS = [3000, 3000, 3000, 3000, 3000];
const CACHE_KEY = "ms_settings_v1";

async function getScopedCacheKey(): Promise<string | null> {
  const scope = await getClientCacheScope({ timeoutMs: SETTINGS_TIMEOUT_MS });
  if (!scope) return null;
  return `${CACHE_KEY}:${scope}`;
}

export function useSettings() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [warmingUp, setWarmingUp] = useState(false);

  // Holds the most recently fetched settings synchronously — updated before
  // React re-renders, so callbacks that fire right after reload() can read
  // fresh data without waiting for the next render cycle.
  const latestSettings = useRef<Settings | null>(null);
  const requestId = useRef(0);
  const abortRef = useRef<AbortController | null>(null);

  const loadSettings = useCallback(async (withRetries: boolean) => {
    const currentRequest = requestId.current + 1;
    requestId.current = currentRequest;
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);
    setWarmingUp(false);

    const attempts = withRetries
      ? SETTINGS_RETRY_DELAYS_MS.length + 1
      : 1;

    for (let attempt = 0; attempt < attempts; attempt += 1) {
      try {
        const next = await getSettings({
          timeoutMs: SETTINGS_TIMEOUT_MS,
          signal: controller.signal,
        });
        if (requestId.current !== currentRequest || controller.signal.aborted) return;
        latestSettings.current = next;
        setSettings(next);
        setError(null);
        setLoading(false);
        setWarmingUp(false);
        try {
          const scopedCacheKey = await getScopedCacheKey();
          if (scopedCacheKey && requestId.current === currentRequest) {
            localStorage.setItem(scopedCacheKey, JSON.stringify(next));
          }
        } catch {
          /* quota/auth timing */
        }
        return;
      } catch (err) {
        if (requestId.current !== currentRequest || controller.signal.aborted) return;
        const message =
          err instanceof Error ? err.message : "Failed to load settings";
        console.error("Failed to load settings:", err);

        if (attempt < attempts - 1) {
          setWarmingUp(true);
          await new Promise<void>((resolve) => {
            const timeout = window.setTimeout(resolve, SETTINGS_RETRY_DELAYS_MS[attempt]);
            controller.signal.addEventListener(
              "abort",
              () => {
                window.clearTimeout(timeout);
                resolve();
              },
              { once: true },
            );
          });
          if (requestId.current !== currentRequest || controller.signal.aborted) return;
          continue;
        }

        // All retries exhausted — fall back to the last cached value so the
        // user at least sees something.  We intentionally do NOT pre-populate
        // from cache on mount (see the useEffect below) because the cache is
        // not scoped by user; showing a previous user's data is worse than a
        // brief loading spinner.
        try {
          const scopedCacheKey = await getScopedCacheKey();
          const cached = scopedCacheKey ? localStorage.getItem(scopedCacheKey) : null;
          if (cached) {
            const fallback = JSON.parse(cached) as Settings;
            if (requestId.current !== currentRequest || controller.signal.aborted) return;
            latestSettings.current = fallback;
            setSettings(fallback);
            setError(`Using cached settings because fresh settings failed: ${message}`);
          } else {
            setSettings(null);
            setError(
              isAuthConfigured() && !scopedCacheKey
                ? "Failed to load settings because authentication was not ready."
                : message,
            );
          }
        } catch {
          setSettings(null);
          setError(message);
        }
        setLoading(false);
        setWarmingUp(false);
      }
    }
  }, []);

  const reload = useCallback(async () => {
    await loadSettings(false);
  }, [loadSettings]);

  useEffect(() => {
    // Always load fresh from the API on mount — never pre-populate from the
    // localStorage cache.  The cache key is not scoped by user, so using it
    // immediately would show the previous user's data to whoever logs in next.
    void loadSettings(true);
    return () => {
      requestId.current += 1;
      abortRef.current?.abort();
    };
  }, [loadSettings]);

  return { settings, latestSettings, loading, error, warmingUp, reload };
}
