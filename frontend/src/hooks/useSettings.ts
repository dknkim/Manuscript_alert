import { useState, useEffect, useCallback } from "react";
import { getSettings } from "@/lib/api";
import type { Settings } from "@/types";

export function useSettings() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    try {
      setSettings(await getSettings());
    } catch (err) {
      console.error("Failed to load settings:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  return { settings, loading, reload };
}
