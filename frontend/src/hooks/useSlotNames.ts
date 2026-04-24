import { useState, useCallback } from "react";
import { MODEL_SLOTS } from "@/hooks/useModelSlots";
import type { SlotKey } from "@/hooks/useModelSlots";

const STORAGE_KEY = "manuscript_slot_names";

function loadFromStorage(): Record<string, string> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Record<string, string>) : {};
  } catch {
    return {};
  }
}

export function useSlotNames() {
  const [slotNames, setSlotNames] = useState<Record<string, string>>(loadFromStorage);

  const setSlotName = useCallback((slotKey: SlotKey, name: string) => {
    setSlotNames((prev) => {
      const next = { ...prev, [slotKey]: name };
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      } catch {
        /* ignore */
      }
      return next;
    });
  }, []);

  const getDisplayName = useCallback(
    (slotKey: SlotKey): string => {
      const custom = slotNames[slotKey];
      if (custom && custom.trim()) return custom.trim();
      return MODEL_SLOTS.find((s) => s.key === slotKey)?.displayName ?? slotKey;
    },
    [slotNames],
  );

  return { slotNames, setSlotName, getDisplayName };
}
