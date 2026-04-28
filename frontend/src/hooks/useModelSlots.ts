import { useState, useEffect, useCallback } from "react";
import { getClientCacheScope, listModels, loadModel, saveModel } from "@/lib/api";

export const MODEL_SLOTS = [
  { key: "Model_1", displayName: "Model #1", saveName: "Model 1" },
  { key: "Model_2", displayName: "Model #2", saveName: "Model 2" },
  { key: "Model_3", displayName: "Model #3", saveName: "Model 3" },
] as const;

export type SlotKey = (typeof MODEL_SLOTS)[number]["key"];

export function getSlotDisplayName(
  slotKey: string,
  customNames?: Partial<Record<string, string>>,
): string {
  const custom = customNames?.[slotKey]?.trim();
  if (custom) return custom;
  return MODEL_SLOTS.find((s) => s.key === slotKey)?.displayName ?? slotKey;
}

const STORAGE_KEY = "manuscript_activeSlot";

async function getStorageKey(): Promise<string> {
  const scope = await getClientCacheScope({ timeoutMs: 5000 });
  return scope ? `${STORAGE_KEY}:${scope}` : `${STORAGE_KEY}:auth-pending`;
}

export function slotKeyFromFilename(filename: string): SlotKey | null {
  const key = filename.replace(".json", "");
  return MODEL_SLOTS.some((slot) => slot.key === key) ? (key as SlotKey) : null;
}

export async function persistActiveSlot(slotKey: SlotKey | null): Promise<void> {
  try {
    const storageKey = await getStorageKey();
    if (slotKey) {
      localStorage.setItem(storageKey, slotKey);
    } else {
      localStorage.removeItem(storageKey);
    }
  } catch {
    /* ignore */
  }
}

export function useModelSlots(onSettingsReload?: () => Promise<void>) {
  // undefined = still loading; Set = loaded (may be empty if none configured or on error)
  const [configuredSlots, setConfiguredSlots] = useState<Set<string> | undefined>(undefined);
  const [activeSlot, setActiveSlot] = useState<SlotKey | null>(null);
  const [busy, setBusy] = useState(false);
  const [storageKey, setStorageKey] = useState<string | null>(null);

  const refreshSlots = useCallback(async () => {
    // Retry on failure so a cold backend startup doesn't permanently mark slots
    // as unconfigured. configuredSlots stays undefined (loading) during retries.
    const retryDelays = [500, 1500, 3000];
    for (let attempt = 0; attempt <= retryDelays.length; attempt++) {
      try {
        const models = await listModels();
        const filenames = new Set(models.map((m) => m.filename.replace(".json", "")));
        const configured = new Set<string>(
          MODEL_SLOTS.map((s) => s.key).filter((k) => filenames.has(k)),
        );
        setConfiguredSlots(configured);
        return;
      } catch {
        if (attempt < retryDelays.length) {
          await new Promise<void>((resolve) =>
            window.setTimeout(resolve, retryDelays[attempt]),
          );
        } else {
          // All retries exhausted — exit loading state so UI doesn't spin forever.
          setConfiguredSlots(new Set());
        }
      }
    }
  }, []);

  useEffect(() => {
    void refreshSlots();
  }, [refreshSlots]);

  useEffect(() => {
    let cancelled = false;
    getStorageKey()
      .then((key) => {
        if (!cancelled) setStorageKey(key);
      })
      .catch(() => {
        if (!cancelled) setStorageKey(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!storageKey) return;
    try {
      const stored = localStorage.getItem(storageKey);
      if (stored && MODEL_SLOTS.some((s) => s.key === stored)) {
        setActiveSlot(stored as SlotKey);
      }
    } catch {
      /* ignore */
    }
  }, [storageKey]);

  // After configuredSlots loads, discard any activeSlot that isn't configured
  // for this user — prevents showing a previous user's active slot.
  useEffect(() => {
    if (configuredSlots === undefined) return;
    if (activeSlot && !configuredSlots.has(activeSlot)) {
      setActiveSlot(null);
      try {
        if (storageKey) localStorage.removeItem(storageKey);
      } catch {
        /* ignore */
      }
    }
  }, [configuredSlots, activeSlot, storageKey]);

  const switchSlot = useCallback(
    async (slotKey: SlotKey) => {
      if (busy) return;
      setBusy(true);
      try {
        await loadModel(slotKey + ".json");
        setActiveSlot(slotKey);
        await persistActiveSlot(slotKey);
        await onSettingsReload?.();
      } finally {
        setBusy(false);
      }
    },
    [busy, onSettingsReload],
  );

  const saveToSlot = useCallback(
    async (slotKey: SlotKey) => {
      if (busy) return;
      setBusy(true);
      try {
        const slot = MODEL_SLOTS.find((s) => s.key === slotKey)!;
        await saveModel(slot.saveName);
        setActiveSlot(slotKey);
        await persistActiveSlot(slotKey);
        await refreshSlots();
      } finally {
        setBusy(false);
      }
    },
    [busy, refreshSlots],
  );

  return { configuredSlots, activeSlot, busy, switchSlot, saveToSlot, refreshSlots };
}
