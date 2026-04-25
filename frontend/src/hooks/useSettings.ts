import { useState, useEffect, useCallback, useRef } from "react";
import { getSettings } from "@/lib/api";
import type { Settings } from "@/types";

const SETTINGS_TIMEOUT_MS = 8000;
const SETTINGS_RETRY_DELAYS_MS = [3000, 3000, 3000, 3000, 3000];
const CACHE_KEY = "ms_settings_v1";

export function useSettings() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [warmingUp, setWarmingUp] = useState(false);

  // Holds the most recently fetched settings synchronously — updated before
  // React re-renders, so callbacks that fire right after reload() can read
  // fresh data without waiting for the next render cycle.
  const latestSettings = useRef<Settings | null>(null);

  const loadSettings = useCallback(async (withRetries: boolean) => {
    setLoading(true);
    setError(null);
    setWarmingUp(false);

    const attempts = withRetries
      ? SETTINGS_RETRY_DELAYS_MS.length + 1
      : 1;

    for (let attempt = 0; attempt < attempts; attempt += 1) {
      try {
        const next = await getSettings({ timeoutMs: SETTINGS_TIMEOUT_MS });
        latestSettings.current = next;
        setSettings(next);
        setError(null);
        setLoading(false);
        setWarmingUp(false);
        try { localStorage.setItem(CACHE_KEY, JSON.stringify(next)); } catch { /* quota */ }
        return;
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to load settings";
        console.error("Failed to load settings:", err);

        if (attempt < attempts - 1) {
          setWarmingUp(true);
          await new Promise((resolve) =>
            window.setTimeout(resolve, SETTINGS_RETRY_DELAYS_MS[attempt]),
          );
          continue;
        }

        // All retries exhausted — fall back to the last cached value so the
        // user at least sees something.  We intentionally do NOT pre-populate
        // from cache on mount (see the useEffect below) because the cache is
        // not scoped by user; showing a previous user's data is worse than a
        // brief loading spinner.
        try {
          const cached = localStorage.getItem(CACHE_KEY);
          if (cached) {
            const fallback = JSON.parse(cached) as Settings;
            latestSettings.current = fallback;
            setSettings(fallback);
            setError(null);
          } else {
            setSettings(null);
            setError(message);
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
  }, [loadSettings]);

  return { settings, latestSettings, loading, error, warmingUp, reload };
}
