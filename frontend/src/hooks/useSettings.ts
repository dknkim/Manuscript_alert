import { useState, useEffect, useCallback } from "react";
import { getSettings } from "@/lib/api";
import type { Settings } from "@/types";

const SETTINGS_TIMEOUT_MS = 12000;
const SETTINGS_RETRY_DELAYS_MS = [1500, 3000];

export function useSettings() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSettings = useCallback(async (withRetries: boolean) => {
    setLoading(true);
    setError(null);

    const attempts = withRetries
      ? SETTINGS_RETRY_DELAYS_MS.length + 1
      : 1;

    for (let attempt = 0; attempt < attempts; attempt += 1) {
      try {
        const next = await getSettings({ timeoutMs: SETTINGS_TIMEOUT_MS });
        setSettings(next);
        setError(null);
        setLoading(false);
        return;
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to load settings";
        console.error("Failed to load settings:", err);

        if (attempt < attempts - 1) {
          await new Promise((resolve) =>
            window.setTimeout(resolve, SETTINGS_RETRY_DELAYS_MS[attempt]),
          );
          continue;
        }

        setSettings(null);
        setError(message);
        setLoading(false);
      }
    }
  }, []);

  const reload = useCallback(async () => {
    await loadSettings(false);
  }, [loadSettings]);

  useEffect(() => {
    void loadSettings(true);
  }, [loadSettings]);

  return { settings, loading, error, reload };
}
