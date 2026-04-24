"use client";

import { useState, useEffect, useCallback } from "react";
import { Search, Newspaper, BarChart2, Archive, Save, FolderPlus } from "lucide-react";
import {
  saveSettings,
  saveModel,
  listBackups,
  restoreBackup,
  createBackup,
} from "@/lib/api";
import type { Settings, BackupInfo, FlashMessage } from "@/types";
import Card from "@/components/ui/Card";
import Flash from "@/components/ui/Flash";
import Toggle from "@/components/ui/Toggle";
import { useModelSlots, MODEL_SLOTS } from "@/hooks/useModelSlots";
import type { SlotKey } from "@/hooks/useModelSlots";

import type { LucideIcon } from "lucide-react";

interface SubTab {
  key: string;
  label: string;
  icon: LucideIcon;
}

const SUB_TABS: SubTab[] = [
  { key: "keywords", label: "Keywords", icon: Search },
  { key: "journals", label: "Journals", icon: Newspaper },
  { key: "scoring", label: "Scoring", icon: BarChart2 },
  { key: "backup", label: "Backup", icon: Archive },
];

interface SettingsTabProps {
  settings: Settings;
  onSettingsChange: () => Promise<void>;
}

export default function SettingsTab({
  settings,
  onSettingsChange,
}: SettingsTabProps) {
  const [sub, setSub] = useState<string>("keywords");
  const [editingSlot, setEditingSlot] = useState<SlotKey | null>(null);
  const slots = useModelSlots(onSettingsChange);
  const [slotMsg, setSlotMsg] = useState<FlashMessage | null>(null);

  // After a sub-tab saves to active settings, also save to the selected slot.
  const handleChange = useCallback(async () => {
    await onSettingsChange();
    if (editingSlot) {
      try {
        await slots.saveToSlot(editingSlot);
      } catch (e: unknown) {
        setSlotMsg({
          type: "error",
          text: `Settings saved but failed to update ${MODEL_SLOTS.find((s) => s.key === editingSlot)?.displayName}: ${e instanceof Error ? e.message : "Unknown error"}`,
        });
        setTimeout(() => setSlotMsg(null), 4000);
      }
    }
  }, [editingSlot, onSettingsChange, slots.saveToSlot]);

  const handleSelectSlot = async (slotKey: SlotKey): Promise<void> => {
    // Don't allow selection while configuredSlots is still loading — we wouldn't
    // know if the slot is configured, so we couldn't load the right settings.
    if (slots.busy || slots.configuredSlots === undefined) return;
    try {
      // Load this slot's settings if it's configured and not already active.
      if (slots.configuredSlots.has(slotKey) && slots.activeSlot !== slotKey) {
        await slots.switchSlot(slotKey);
      }
      setEditingSlot(slotKey);
      setSlotMsg(null);
    } catch (e: unknown) {
      setSlotMsg({
        type: "error",
        text: e instanceof Error ? e.message : "Failed to load slot",
      });
      setTimeout(() => setSlotMsg(null), 3000);
    }
  };

  const editingSlotLabel = MODEL_SLOTS.find((s) => s.key === editingSlot)?.displayName;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 pt-6 space-y-6">
      <div>
        <h2 className="text-xl font-bold text-text-primary">
          ⚙️ Application Settings
        </h2>
        <p className="text-sm text-text-muted mt-1">
          Select a model slot to configure, then edit keywords, journals, and
          scoring below.
        </p>
      </div>

      {/* Slot picker */}
      <div className="bg-surface-raised rounded-xl border border-border p-5">
        <h3 className="text-sm font-semibold text-text-primary mb-0.5">
          Which model would you like to configure?
        </h3>
        <p className="text-xs text-text-muted mb-4">
          Selecting a slot loads its settings for editing. Each save will update
          both the slot and your active configuration.
        </p>

        {slotMsg && (
          <div
            className={`mb-4 px-3 py-2 rounded-lg text-xs ${
              slotMsg.type === "error"
                ? "bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300"
                : "bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-300"
            }`}
          >
            {slotMsg.text}
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {MODEL_SLOTS.map((slot) => {
            const slotsLoading = slots.configuredSlots === undefined;
            const isConfigured = !slotsLoading && (slots.configuredSlots?.has(slot.key) ?? false);
            const isEditing = editingSlot === slot.key;
            return (
              <button
                key={slot.key}
                disabled={slots.busy || slotsLoading}
                onClick={() => void handleSelectSlot(slot.key)}
                className={`p-4 rounded-xl border text-left transition-all disabled:opacity-50 ${
                  isEditing
                    ? "border-accent ring-2 ring-accent/20 bg-accent-subtle"
                    : isConfigured
                      ? "border-border bg-surface hover:border-accent/50 hover:bg-surface-inset"
                      : "border-dashed border-border bg-surface hover:border-accent/50 hover:bg-surface-inset"
                }`}
              >
                <p
                  className={`text-sm font-semibold ${
                    isEditing ? "text-accent-text" : "text-text-primary"
                  }`}
                >
                  {slot.displayName}
                </p>
                <p className="text-xs text-text-muted mt-0.5">
                  {slotsLoading ? "Loading…" : isConfigured ? "Configured" : "Not set up yet"}
                </p>
                {isEditing && (
                  <p className="text-xs text-accent font-medium mt-1">
                    ✓ Editing now
                  </p>
                )}
              </button>
            );
          })}
        </div>

        {editingSlot ? (
          <div className="mt-3 flex items-center justify-between">
            <p className="text-xs text-text-muted">
              Saves below will also update{" "}
              <span className="font-medium text-text-primary">
                {editingSlotLabel}
              </span>
              .
            </p>
            <button
              onClick={() => setEditingSlot(null)}
              className="text-xs text-text-muted hover:text-text-secondary transition-colors"
            >
              Clear selection
            </button>
          </div>
        ) : (
          <p className="mt-3 text-xs text-text-muted">
            No slot selected — saves will only update your active configuration.
          </p>
        )}
      </div>

      {/* Sub-tab nav */}
      <div className="sticky z-20 bg-surface flex border-b border-border" style={{ top: "var(--header-h, 64px)" }}>
        {SUB_TABS.map((t) => {
          const Icon = t.icon;
          const active = sub === t.key;
          return (
            <button
              key={t.key}
              onClick={() => setSub(t.key)}
              className={`flex-1 flex items-center justify-center gap-1.5 px-2 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px ${
                active
                  ? "border-accent text-accent"
                  : "border-transparent text-text-muted hover:text-text-secondary"
              }`}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span className="hidden sm:inline">{t.label}</span>
            </button>
          );
        })}
      </div>

      {sub === "keywords" && (
        <KeywordSettings
          settings={settings}
          onChange={handleChange}
          editingSlot={editingSlot}
        />
      )}
      {sub === "journals" && (
        <JournalSettings
          settings={settings}
          onChange={handleChange}
          editingSlot={editingSlot}
        />
      )}
      {sub === "scoring" && (
        <ScoringSettings
          settings={settings}
          onChange={handleChange}
          editingSlot={editingSlot}
        />
      )}
      {sub === "backup" && <BackupSettings />}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   Keywords sub-tab
   ───────────────────────────────────────────────────────────── */

function KeywordSettings({
  settings,
  onChange,
  editingSlot,
}: {
  settings: Settings;
  onChange: () => Promise<void>;
  editingSlot: SlotKey | null;
}) {
  const [keywordsText, setKeywordsText] = useState<string>(
    (settings.keywords || []).join("\n"),
  );
  const [highPriority, setHighPriority] = useState<string[]>(
    settings.keyword_scoring?.high_priority?.keywords || [],
  );
  const [mediumPriority, setMediumPriority] = useState<string[]>(
    settings.keyword_scoring?.medium_priority?.keywords || [],
  );
  const [mustHave, setMustHave] = useState<string[]>(
    settings.must_have_keywords || [],
  );
  const [msg, setMsg] = useState<FlashMessage | null>(null);

  // Sync local state when settings change (e.g. after loading a model)
  useEffect(() => {
    setKeywordsText((settings.keywords || []).join("\n"));
    setHighPriority(
      settings.keyword_scoring?.high_priority?.keywords || [],
    );
    setMediumPriority(
      settings.keyword_scoring?.medium_priority?.keywords || [],
    );
    setMustHave(settings.must_have_keywords || []);
  }, [settings]);

  const allKeywords = keywordsText
    .split("\n")
    .map((k) => k.trim())
    .filter(Boolean);

  const handleSave = async (): Promise<void> => {
    try {
      const updated: Settings = {
        ...settings,
        keywords: allKeywords,
        keyword_scoring: {
          high_priority: { keywords: highPriority, boost: 1.5 },
          medium_priority: { keywords: mediumPriority, boost: 1.2 },
        },
        must_have_keywords: mustHave,
      };
      await saveSettings(updated);
      setMsg({ type: "success", text: "Keywords configuration saved!" });
      onChange();
    } catch (e: unknown) {
      setMsg({
        type: "error",
        text: e instanceof Error ? e.message : "Unknown error",
      });
    }
  };

  return (
    <div className="space-y-6 pb-14 lg:pb-0">
      <Flash msg={msg} onClear={() => setMsg(null)} />

      <Card
        title="Research Keywords"
        desc="Papers must match at least 2 keywords."
      >
        <textarea
          value={keywordsText}
          onChange={(e) => setKeywordsText(e.target.value)}
          rows={8}
          className="w-full px-3 py-2 border border-border bg-surface rounded-lg text-sm text-text-primary focus:ring-2 focus:ring-accent focus:border-accent outline-hidden font-mono"
          placeholder="One keyword per line"
        />
      </Card>

      <Card title="Keyword Priority Scoring">
        <MultiSelect
          label="High Priority (1.5x boost)"
          options={allKeywords}
          selected={highPriority}
          onChange={setHighPriority}
          exclude={mediumPriority}
        />
        <MultiSelect
          label="Medium Priority (1.2x boost)"
          options={allKeywords.filter((k) => !highPriority.includes(k))}
          selected={mediumPriority}
          onChange={setMediumPriority}
          exclude={highPriority}
        />
        {allKeywords.filter(
          (k) => !highPriority.includes(k) && !mediumPriority.includes(k),
        ).length > 0 && (
          <p className="text-sm text-text-muted mt-2">
            Default priority:{" "}
            {allKeywords
              .filter(
                (k) =>
                  !highPriority.includes(k) && !mediumPriority.includes(k),
              )
              .join(", ")}
          </p>
        )}
      </Card>

      <Card
        title="Must Have Keywords (Optional)"
        desc="Papers must match at least one of these to appear."
      >
        <MultiSelect
          label="Must Have"
          options={allKeywords}
          selected={mustHave}
          onChange={setMustHave}
        />
        {mustHave.length > 0 && (
          <p className="text-xs text-amber-600 mt-2">
            ⚠️ Papers not matching any of these will be excluded.
          </p>
        )}
      </Card>

      <div className="fixed bottom-14 left-0 right-0 z-20 lg:sticky lg:bottom-0 lg:left-auto lg:right-auto -mx-0 lg:-mx-6 px-6 pt-3 pb-5 bg-surface border-t border-border flex justify-end">
        <button
          onClick={handleSave}
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm font-semibold transition-colors"
        >
          <Save className="w-4 h-4 shrink-0" />
          {editingSlot
            ? `Save to ${MODEL_SLOTS.find((s) => s.key === editingSlot)?.displayName}`
            : "Save Keywords Configuration"}
        </button>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   Journals sub-tab
   ───────────────────────────────────────────────────────────── */

function JournalSettings({
  settings,
  onChange,
  editingSlot,
}: {
  settings: Settings;
  onChange: () => Promise<void>;
  editingSlot: SlotKey | null;
}) {
  const tj = settings.target_journals || {
    exact_matches: [],
    family_matches: [],
    specific_journals: [],
  };
  const [exact, setExact] = useState<string>(
    (tj.exact_matches || []).join("\n"),
  );
  const [family, setFamily] = useState<string>(
    (tj.family_matches || []).join("\n"),
  );
  const [specific, setSpecific] = useState<string>(
    (tj.specific_journals || []).join("\n"),
  );
  const excl = settings.journal_exclusions || [];
  const [exclusions, setExclusions] = useState<string>(
    Array.isArray(excl) ? excl.join("\n") : "",
  );
  const [msg, setMsg] = useState<FlashMessage | null>(null);

  // Sync local state when settings change (e.g. after loading a model)
  useEffect(() => {
    const tj = settings.target_journals || {
      exact_matches: [],
      family_matches: [],
      specific_journals: [],
    };
    setExact((tj.exact_matches || []).join("\n"));
    setFamily((tj.family_matches || []).join("\n"));
    setSpecific((tj.specific_journals || []).join("\n"));
    const excl = settings.journal_exclusions || [];
    setExclusions(Array.isArray(excl) ? excl.join("\n") : "");
  }, [settings]);

  const handleSave = async (): Promise<void> => {
    try {
      const updated: Settings = {
        ...settings,
        target_journals: {
          exact_matches: lines(exact),
          family_matches: lines(family),
          specific_journals: lines(specific),
        },
        journal_exclusions: lines(exclusions),
      };
      await saveSettings(updated);
      setMsg({ type: "success", text: "Journal configuration saved!" });
      onChange();
    } catch (e: unknown) {
      setMsg({
        type: "error",
        text: e instanceof Error ? e.message : "Unknown error",
      });
    }
  };

  return (
    <div className="space-y-6 pb-14 lg:pb-0">
      <Flash msg={msg} onClear={() => setMsg(null)} />

      <Card title="Target Journals">
        <label className="block text-sm font-medium text-text-secondary mb-1">
          Exact Matches (highest priority)
        </label>
        <textarea
          value={exact}
          onChange={(e) => setExact(e.target.value)}
          rows={4}
          className="w-full px-3 py-2 border border-border bg-surface rounded-lg text-sm text-text-primary focus:ring-2 focus:ring-accent focus:border-accent outline-hidden font-mono mb-4"
        />

        <label className="block text-sm font-medium text-text-secondary mb-1">
          Family Matches (medium priority)
        </label>
        <textarea
          value={family}
          onChange={(e) => setFamily(e.target.value)}
          rows={4}
          className="w-full px-3 py-2 border border-border bg-surface rounded-lg text-sm text-text-primary focus:ring-2 focus:ring-accent focus:border-accent outline-hidden font-mono mb-4"
        />

        <label className="block text-sm font-medium text-text-secondary mb-1">
          Specific Journals (lower priority)
        </label>
        <textarea
          value={specific}
          onChange={(e) => setSpecific(e.target.value)}
          rows={6}
          className="w-full px-3 py-2 border border-border bg-surface rounded-lg text-sm text-text-primary focus:ring-2 focus:ring-accent focus:border-accent outline-hidden font-mono"
        />
      </Card>

      <Card
        title="Journal Exclusions"
        desc="Any journal containing these patterns will be excluded from scoring."
      >
        <textarea
          value={exclusions}
          onChange={(e) => setExclusions(e.target.value)}
          rows={8}
          className="w-full px-3 py-2 border border-border bg-surface rounded-lg text-sm text-text-primary focus:ring-2 focus:ring-accent focus:border-accent outline-hidden font-mono"
          placeholder="One pattern per line"
        />
      </Card>

      <div className="fixed bottom-14 left-0 right-0 z-20 lg:sticky lg:bottom-0 lg:left-auto lg:right-auto -mx-0 lg:-mx-6 px-6 pt-3 pb-5 bg-surface border-t border-border flex justify-end">
        <button
          onClick={handleSave}
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm font-semibold transition-colors"
        >
          <Save className="w-4 h-4 shrink-0" />
          {editingSlot
            ? `Save to ${MODEL_SLOTS.find((s) => s.key === editingSlot)?.displayName}`
            : "Save Journal Configuration"}
        </button>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   Scoring sub-tab
   ───────────────────────────────────────────────────────────── */

function ScoringSettings({
  settings,
  onChange,
  editingSlot,
}: {
  settings: Settings;
  onChange: () => Promise<void>;
  editingSlot: SlotKey | null;
}) {
  const js = settings.journal_scoring || { enabled: true, high_impact_journal_boost: {} };
  const [enabled, setEnabled] = useState<boolean>(js.enabled ?? true);
  const boosts = js.high_impact_journal_boost || {};
  const [b5, setB5] = useState<number>(boosts["5_or_more_keywords"] ?? 5.1);
  const [b4, setB4] = useState<number>(boosts["4_keywords"] ?? 3.7);
  const [b3, setB3] = useState<number>(boosts["3_keywords"] ?? 2.8);
  const [b2, setB2] = useState<number>(boosts["2_keywords"] ?? 1.3);
  const [b1, setB1] = useState<number>(boosts["1_keyword"] ?? 0.5);

  const ss = settings.search_settings || ({} as Settings["search_settings"]);
  const [daysBack, setDaysBack] = useState<number>(ss.days_back ?? 7);
  const [minKw, setMinKw] = useState<number>(ss.min_keyword_matches ?? 2);
  const [mode, setMode] = useState<string>(ss.search_mode ?? "Brief");
  const [maxResults, setMaxResults] = useState<number>(
    ss.max_results_display ?? 50,
  );

  const ds = ss.default_sources || { pubmed: true, arxiv: false, biorxiv: false, medrxiv: false };
  const [sPubmed, setSPubmed] = useState<boolean>(ds.pubmed ?? true);
  const [sArxiv, setSArxiv] = useState<boolean>(ds.arxiv ?? false);
  const [sBiorxiv, setSBiorxiv] = useState<boolean>(ds.biorxiv ?? false);
  const [sMedrxiv, setSMedrxiv] = useState<boolean>(ds.medrxiv ?? false);

  const [msg, setMsg] = useState<FlashMessage | null>(null);

  // Sync local state when settings change (e.g. after loading a model)
  useEffect(() => {
    const js = settings.journal_scoring || { enabled: true, high_impact_journal_boost: {} };
    setEnabled(js.enabled ?? true);
    const boosts = js.high_impact_journal_boost || {};
    setB5(boosts["5_or_more_keywords"] ?? 5.1);
    setB4(boosts["4_keywords"] ?? 3.7);
    setB3(boosts["3_keywords"] ?? 2.8);
    setB2(boosts["2_keywords"] ?? 1.3);
    setB1(boosts["1_keyword"] ?? 0.5);

    const ss = settings.search_settings || ({} as Settings["search_settings"]);
    setDaysBack(ss.days_back ?? 7);
    setMinKw(ss.min_keyword_matches ?? 2);
    setMode(ss.search_mode ?? "Brief");
    setMaxResults(ss.max_results_display ?? 50);

    const ds = ss.default_sources || { pubmed: true, arxiv: false, biorxiv: false, medrxiv: false };
    setSPubmed(ds.pubmed ?? true);
    setSArxiv(ds.arxiv ?? false);
    setSBiorxiv(ds.biorxiv ?? false);
    setSMedrxiv(ds.medrxiv ?? false);
  }, [settings]);

  const handleSave = async (): Promise<void> => {
    try {
      const updated: Settings = {
        ...settings,
        journal_scoring: enabled
          ? {
              enabled: true,
              high_impact_journal_boost: {
                "5_or_more_keywords": Number(b5),
                "4_keywords": Number(b4),
                "3_keywords": Number(b3),
                "2_keywords": Number(b2),
                "1_keyword": Number(b1),
              },
            }
          : { enabled: false, high_impact_journal_boost: {} },
        search_settings: {
          days_back: Number(daysBack),
          search_mode: mode,
          min_keyword_matches: Number(minKw),
          max_results_display: Number(maxResults),
          default_sources: {
            pubmed: sPubmed,
            arxiv: sArxiv,
            biorxiv: sBiorxiv,
            medrxiv: sMedrxiv,
          },
          journal_quality_filter:
            settings.search_settings?.journal_quality_filter ?? false,
        },
      };
      await saveSettings(updated);
      setMsg({ type: "success", text: "Scoring configuration saved!" });
      onChange();
    } catch (e: unknown) {
      setMsg({
        type: "error",
        text: e instanceof Error ? e.message : "Unknown error",
      });
    }
  };

  return (
    <div className="space-y-6 pb-14 lg:pb-0">
      <Flash msg={msg} onClear={() => setMsg(null)} />

      <Card title="Journal Impact Scoring">
        <label className="flex items-center gap-2 mb-4 cursor-pointer">
          <input
            type="checkbox"
            checked={enabled}
            onChange={() => setEnabled(!enabled)}
            className="rounded border-border text-accent focus:ring-accent"
          />
          <span className="text-sm text-text-secondary">
            Enable Journal Impact Scoring
          </span>
        </label>

        {enabled && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <NumField label="5+ keywords" value={b5} onChange={setB5} />
            <NumField label="4 keywords" value={b4} onChange={setB4} />
            <NumField label="3 keywords" value={b3} onChange={setB3} />
            <NumField label="2 keywords" value={b2} onChange={setB2} />
            <NumField label="1 keyword" value={b1} onChange={setB1} />
          </div>
        )}
      </Card>

      <Card title="Search Configuration">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <NumField
            label="Days Back"
            value={daysBack}
            onChange={setDaysBack}
            min={1}
            max={30}
            step={1}
          />
          <NumField
            label="Min Keyword Matches"
            value={minKw}
            onChange={setMinKw}
            min={1}
            max={10}
            step={1}
          />
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">
              Default Search Mode
            </label>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              className="w-full px-3 py-2 border border-border bg-surface rounded-lg text-sm text-text-primary focus:ring-2 focus:ring-accent focus:border-accent outline-hidden"
            >
              <option>Brief</option>
              <option>Standard</option>
              <option>Extended</option>
            </select>
          </div>
          <NumField
            label="Max Results Display"
            value={maxResults}
            onChange={setMaxResults}
            min={10}
            max={200}
            step={10}
          />
        </div>
      </Card>

      <Card title="Default Data Sources">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Toggle label="PubMed" checked={sPubmed} onChange={setSPubmed} />
          <Toggle label="arXiv" checked={sArxiv} onChange={setSArxiv} />
          <Toggle label="bioRxiv" checked={sBiorxiv} onChange={setSBiorxiv} />
          <Toggle label="medRxiv" checked={sMedrxiv} onChange={setSMedrxiv} />
        </div>
      </Card>

      <div className="fixed bottom-14 left-0 right-0 z-20 lg:sticky lg:bottom-0 lg:left-auto lg:right-auto -mx-0 lg:-mx-6 px-6 pt-3 pb-5 bg-surface border-t border-border flex justify-end">
        <button
          onClick={handleSave}
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm font-semibold transition-colors"
        >
          <Save className="w-4 h-4 shrink-0" />
          {editingSlot
            ? `Save to ${MODEL_SLOTS.find((s) => s.key === editingSlot)?.displayName}`
            : "Save Scoring Configuration"}
        </button>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   Backup sub-tab
   ───────────────────────────────────────────────────────────── */

function BackupSettings() {
  const [backups, setBackups] = useState<BackupInfo[]>([]);
  const [msg, setMsg] = useState<FlashMessage | null>(null);

  const refresh = async (): Promise<void> => {
    try {
      const data = await listBackups();
      setBackups(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const flash = (text: string, type: "success" | "error" = "success"): void => {
    setMsg({ text, type });
    setTimeout(() => setMsg(null), 4000);
  };

  const handleRestore = async (path: string): Promise<void> => {
    try {
      await restoreBackup(path);
      flash("Backup restored successfully!");
    } catch (e: unknown) {
      flash(e instanceof Error ? e.message : "Unknown error", "error");
    }
  };

  const handleCreate = async (): Promise<void> => {
    try {
      await createBackup();
      flash("Manual backup created.");
      refresh();
    } catch (e: unknown) {
      flash(e instanceof Error ? e.message : "Unknown error", "error");
    }
  };

  return (
    <div className="space-y-6 pb-14 lg:pb-0">
      <Flash msg={msg} onClear={() => setMsg(null)} />

      <Card title="Available Backups">
        {backups.length === 0 ? (
          <p className="text-sm text-text-muted py-4 text-center">
            No backups found. Backups are created automatically when you save
            settings.
          </p>
        ) : (
          <div className="divide-y divide-border">
            {backups.map((b, i) => (
              <div
                key={b.path}
                className="flex items-center justify-between py-2.5"
              >
                <span className="text-sm text-text-secondary">
                  Backup {i + 1}: {b.date}
                </span>
                <button
                  onClick={() => handleRestore(b.path)}
                  className="px-3 py-1.5 bg-accent-subtle text-accent-text hover:bg-accent-subtle/80 rounded-md text-xs font-medium transition-colors"
                >
                  Restore
                </button>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card title="Create Manual Backup">
        <button
          onClick={handleCreate}
          className="inline-flex items-center gap-2 px-5 py-2 border border-border rounded-lg text-sm font-medium text-text-secondary hover:bg-surface-inset transition-colors"
        >
          <FolderPlus className="w-4 h-4" /> Create Backup Now
        </button>
      </Card>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   Local helpers
   ───────────────────────────────────────────────────────────── */

function NumField({
  label,
  value,
  onChange,
  min,
  max,
  step = 0.1,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-text-secondary mb-1">
        {label}
      </label>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        min={min}
        max={max}
        step={step}
        className="w-full px-3 py-2 border border-border bg-surface rounded-lg text-sm text-text-primary focus:ring-2 focus:ring-accent focus:border-accent outline-hidden"
      />
    </div>
  );
}

function MultiSelect({
  label,
  options,
  selected,
  onChange,
  exclude = [],
}: {
  label: string;
  options: string[];
  selected: string[];
  onChange: (v: string[]) => void;
  exclude?: string[];
}) {
  const available = options.filter((o) => !exclude.includes(o));

  const toggle = (item: string): void => {
    if (selected.includes(item)) {
      onChange(selected.filter((s) => s !== item));
    } else {
      onChange([...selected, item]);
    }
  };

  return (
    <div className="mb-3">
      <label className="block text-sm font-medium text-text-secondary mb-1.5">
        {label}
      </label>
      <div className="flex flex-wrap gap-1.5">
        {available.map((opt) => {
          const active = selected.includes(opt);
          return (
            <button
              key={opt}
              onClick={() => toggle(opt)}
              className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors border ${
                active
                  ? "bg-accent-subtle text-accent-text border-accent/30"
                  : "bg-surface-inset text-text-muted border-border hover:bg-surface-inset/80"
              }`}
            >
              {active && "✓ "}
              {opt}
            </button>
          );
        })}
        {available.length === 0 && (
          <span className="text-xs text-text-muted">No options available</span>
        )}
      </div>
    </div>
  );
}

function lines(text: string): string[] {
  return text
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
}
