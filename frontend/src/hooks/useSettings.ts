import { useState, useEffect, useCallback } from "react";
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

        setSettings(null);
        setError(message);
        setLoading(false);
        setWarmingUp(false);
      }
    }
  }, []);

  const reload = useCallback(async () => {
    await loadSettings(false);
  }, [loadSettings]);

  useEffect(() => {
    try {
      const cached = localStorage.getItem(CACHE_KEY);
      if (cached) {
        setSettings(JSON.parse(cached) as Settings);
        setLoading(false);
      }
    } catch { /* ignore */ }
    void loadSettings(true);
  }, [loadSettings]);

  return { settings, loading, error, warmingUp, reload };
}
