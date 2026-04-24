import { useState, useEffect, useCallback } from "react";
import { listModels, loadModel, saveModel } from "@/lib/api";

export const MODEL_SLOTS = [
  { key: "Model_1", displayName: "Model #1", saveName: "Model 1" },
  { key: "Model_2", displayName: "Model #2", saveName: "Model 2" },
  { key: "Model_3", displayName: "Model #3", saveName: "Model 3" },
] as const;

export type SlotKey = (typeof MODEL_SLOTS)[number]["key"];

const STORAGE_KEY = "manuscript_activeSlot";

export function useModelSlots(onSettingsReload?: () => Promise<void>) {
  // undefined = still loading; Set = loaded (may be empty if none configured or on error)
  const [configuredSlots, setConfiguredSlots] = useState<Set<string> | undefined>(undefined);
  const [activeSlot, setActiveSlot] = useState<SlotKey | null>(null);
  const [busy, setBusy] = useState(false);

  const refreshSlots = useCallback(async () => {
    try {
      const models = await listModels();
      const filenames = new Set(models.map((m) => m.filename.replace(".json", "")));
      const configured = new Set<string>(
        MODEL_SLOTS.map((s) => s.key).filter((k) => filenames.has(k)),
      );
      setConfiguredSlots(configured);
    } catch {
      // On error, mark as loaded-but-empty so callers don't stay in "loading" forever.
      setConfiguredSlots(new Set());
    }
  }, []);

  useEffect(() => {
    void refreshSlots();
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored && MODEL_SLOTS.some((s) => s.key === stored)) {
        setActiveSlot(stored as SlotKey);
      }
    } catch {
      /* ignore */
    }
  }, [refreshSlots]);

  const switchSlot = useCallback(
    async (slotKey: SlotKey) => {
      if (busy) return;
      setBusy(true);
      try {
        await loadModel(slotKey + ".json");
        setActiveSlot(slotKey);
        try {
          localStorage.setItem(STORAGE_KEY, slotKey);
        } catch {
          /* ignore */
        }
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
        try {
          localStorage.setItem(STORAGE_KEY, slotKey);
        } catch {
          /* ignore */
        }
        await refreshSlots();
      } finally {
        setBusy(false);
      }
    },
    [busy, refreshSlots],
  );

  return { configuredSlots, activeSlot, busy, switchSlot, saveToSlot, refreshSlots };
}
