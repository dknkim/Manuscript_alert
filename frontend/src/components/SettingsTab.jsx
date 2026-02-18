import React, { useState, useEffect } from "react";
import {
  saveSettings,
  listBackups,
  restoreBackup,
  createBackup,
} from "../api";

const SUB_TABS = [
  { key: "keywords", label: "🔍 Keywords" },
  { key: "journals", label: "📰 Journals" },
  { key: "scoring", label: "📊 Scoring" },
  { key: "backup", label: "💾 Backup" },
];

export default function SettingsTab({ settings, onSettingsChange }) {
  const [sub, setSub] = useState("keywords");

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900">
          ⚙️ Application Settings
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          Configure keywords, journal selections, and scoring parameters.
          Changes persist across runs.
        </p>
      </div>

      {/* Sub-tab nav */}
      <div className="flex gap-1 border-b border-gray-200">
        {SUB_TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setSub(t.key)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px ${
              sub === t.key
                ? "border-indigo-600 text-indigo-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {sub === "keywords" && (
        <KeywordSettings settings={settings} onChange={onSettingsChange} />
      )}
      {sub === "journals" && (
        <JournalSettings settings={settings} onChange={onSettingsChange} />
      )}
      {sub === "scoring" && (
        <ScoringSettings settings={settings} onChange={onSettingsChange} />
      )}
      {sub === "backup" && <BackupSettings />}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Keywords sub-tab
// ---------------------------------------------------------------------------
function KeywordSettings({ settings, onChange }) {
  const [keywordsText, setKeywordsText] = useState(
    (settings.keywords || []).join("\n")
  );
  const [highPriority, setHighPriority] = useState(
    settings.keyword_scoring?.high_priority?.keywords || []
  );
  const [mediumPriority, setMediumPriority] = useState(
    settings.keyword_scoring?.medium_priority?.keywords || []
  );
  const [mustHave, setMustHave] = useState(
    settings.must_have_keywords || []
  );
  const [msg, setMsg] = useState(null);

  // Sync local state when settings change (e.g. after loading a model)
  useEffect(() => {
    setKeywordsText((settings.keywords || []).join("\n"));
    setHighPriority(settings.keyword_scoring?.high_priority?.keywords || []);
    setMediumPriority(settings.keyword_scoring?.medium_priority?.keywords || []);
    setMustHave(settings.must_have_keywords || []);
  }, [settings]);

  const allKeywords = keywordsText
    .split("\n")
    .map((k) => k.trim())
    .filter(Boolean);

  const handleSave = async () => {
    try {
      const updated = {
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
    } catch (e) {
      setMsg({ type: "error", text: e.message });
    }
  };

  return (
    <div className="space-y-6">
      <Flash msg={msg} onClear={() => setMsg(null)} />

      <Card title="Research Keywords" desc="Papers must match at least 2 keywords.">
        <textarea
          value={keywordsText}
          onChange={(e) => setKeywordsText(e.target.value)}
          rows={8}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none font-mono"
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
          (k) => !highPriority.includes(k) && !mediumPriority.includes(k)
        ).length > 0 && (
          <p className="text-sm text-gray-400 mt-2">
            Default priority:{" "}
            {allKeywords
              .filter(
                (k) => !highPriority.includes(k) && !mediumPriority.includes(k)
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

      <button
        onClick={handleSave}
        className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold transition-colors"
      >
        💾 Save Keywords Configuration
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Journals sub-tab
// ---------------------------------------------------------------------------
function JournalSettings({ settings, onChange }) {
  const tj = settings.target_journals || {};
  const [exact, setExact] = useState((tj.exact_matches || []).join("\n"));
  const [family, setFamily] = useState((tj.family_matches || []).join("\n"));
  const [specific, setSpecific] = useState(
    (tj.specific_journals || []).join("\n")
  );

  const excl = settings.journal_exclusions || [];
  const [exclusions, setExclusions] = useState(
    Array.isArray(excl) ? excl.join("\n") : ""
  );
  const [msg, setMsg] = useState(null);

  // Sync local state when settings change (e.g. after loading a model)
  useEffect(() => {
    const tj = settings.target_journals || {};
    setExact((tj.exact_matches || []).join("\n"));
    setFamily((tj.family_matches || []).join("\n"));
    setSpecific((tj.specific_journals || []).join("\n"));
    const excl = settings.journal_exclusions || [];
    setExclusions(Array.isArray(excl) ? excl.join("\n") : "");
  }, [settings]);

  const handleSave = async () => {
    try {
      const updated = {
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
    } catch (e) {
      setMsg({ type: "error", text: e.message });
    }
  };

  return (
    <div className="space-y-6">
      <Flash msg={msg} onClear={() => setMsg(null)} />

      <Card title="Target Journals">
        <label className="block text-sm font-medium text-gray-600 mb-1">
          Exact Matches (highest priority)
        </label>
        <textarea
          value={exact}
          onChange={(e) => setExact(e.target.value)}
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none font-mono mb-4"
        />

        <label className="block text-sm font-medium text-gray-600 mb-1">
          Family Matches (medium priority)
        </label>
        <textarea
          value={family}
          onChange={(e) => setFamily(e.target.value)}
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none font-mono mb-4"
        />

        <label className="block text-sm font-medium text-gray-600 mb-1">
          Specific Journals (lower priority)
        </label>
        <textarea
          value={specific}
          onChange={(e) => setSpecific(e.target.value)}
          rows={6}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none font-mono"
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
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none font-mono"
          placeholder="One pattern per line"
        />
      </Card>

      <button
        onClick={handleSave}
        className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold transition-colors"
      >
        💾 Save Journal Configuration
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Scoring sub-tab
// ---------------------------------------------------------------------------
function ScoringSettings({ settings, onChange }) {
  const js = settings.journal_scoring || {};
  const [enabled, setEnabled] = useState(js.enabled ?? true);
  const boosts = js.high_impact_journal_boost || {};
  const [b5, setB5] = useState(boosts["5_or_more_keywords"] ?? 5.1);
  const [b4, setB4] = useState(boosts["4_keywords"] ?? 3.7);
  const [b3, setB3] = useState(boosts["3_keywords"] ?? 2.8);
  const [b2, setB2] = useState(boosts["2_keywords"] ?? 1.3);
  const [b1, setB1] = useState(boosts["1_keyword"] ?? 0.5);

  const ss = settings.search_settings || {};
  const [daysBack, setDaysBack] = useState(ss.days_back ?? 7);
  const [minKw, setMinKw] = useState(ss.min_keyword_matches ?? 2);
  const [mode, setMode] = useState(ss.search_mode ?? "Brief");
  const [maxResults, setMaxResults] = useState(ss.max_results_display ?? 50);

  const ds = ss.default_sources || {};
  const [sPubmed, setSPubmed] = useState(ds.pubmed ?? true);
  const [sArxiv, setSArxiv] = useState(ds.arxiv ?? false);
  const [sBiorxiv, setSBiorxiv] = useState(ds.biorxiv ?? false);
  const [sMedrxiv, setSMedrxiv] = useState(ds.medrxiv ?? false);

  const [msg, setMsg] = useState(null);

  // Sync local state when settings change (e.g. after loading a model)
  useEffect(() => {
    const js = settings.journal_scoring || {};
    setEnabled(js.enabled ?? true);
    const boosts = js.high_impact_journal_boost || {};
    setB5(boosts["5_or_more_keywords"] ?? 5.1);
    setB4(boosts["4_keywords"] ?? 3.7);
    setB3(boosts["3_keywords"] ?? 2.8);
    setB2(boosts["2_keywords"] ?? 1.3);
    setB1(boosts["1_keyword"] ?? 0.5);

    const ss = settings.search_settings || {};
    setDaysBack(ss.days_back ?? 7);
    setMinKw(ss.min_keyword_matches ?? 2);
    setMode(ss.search_mode ?? "Brief");
    setMaxResults(ss.max_results_display ?? 50);

    const ds = ss.default_sources || {};
    setSPubmed(ds.pubmed ?? true);
    setSArxiv(ds.arxiv ?? false);
    setSBiorxiv(ds.biorxiv ?? false);
    setSMedrxiv(ds.medrxiv ?? false);
  }, [settings]);

  const handleSave = async () => {
    try {
      const updated = {
        ...settings,
        journal_scoring: enabled
          ? {
              enabled: true,
              high_impact_journal_boost: {
                "5_or_more_keywords": parseFloat(b5),
                "4_keywords": parseFloat(b4),
                "3_keywords": parseFloat(b3),
                "2_keywords": parseFloat(b2),
                "1_keyword": parseFloat(b1),
              },
            }
          : { enabled: false },
        search_settings: {
          days_back: parseInt(daysBack, 10),
          search_mode: mode,
          min_keyword_matches: parseInt(minKw, 10),
          max_results_display: parseInt(maxResults, 10),
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
    } catch (e) {
      setMsg({ type: "error", text: e.message });
    }
  };

  return (
    <div className="space-y-6">
      <Flash msg={msg} onClear={() => setMsg(null)} />

      <Card title="Journal Impact Scoring">
        <label className="flex items-center gap-2 mb-4 cursor-pointer">
          <input
            type="checkbox"
            checked={enabled}
            onChange={() => setEnabled(!enabled)}
            className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
          />
          <span className="text-sm text-gray-700">
            Enable Journal Impact Scoring
          </span>
        </label>

        {enabled && (
          <div className="grid grid-cols-2 gap-4">
            <NumField label="5+ keywords" value={b5} onChange={setB5} />
            <NumField label="4 keywords" value={b4} onChange={setB4} />
            <NumField label="3 keywords" value={b3} onChange={setB3} />
            <NumField label="2 keywords" value={b2} onChange={setB2} />
            <NumField label="1 keyword" value={b1} onChange={setB1} />
          </div>
        )}
      </Card>

      <Card title="Search Configuration">
        <div className="grid grid-cols-2 gap-4">
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
            <label className="block text-sm font-medium text-gray-600 mb-1">
              Default Search Mode
            </label>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
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
        <div className="grid grid-cols-2 gap-3">
          <Toggle label="PubMed" checked={sPubmed} onChange={setSPubmed} />
          <Toggle label="arXiv" checked={sArxiv} onChange={setSArxiv} />
          <Toggle label="bioRxiv" checked={sBiorxiv} onChange={setSBiorxiv} />
          <Toggle label="medRxiv" checked={sMedrxiv} onChange={setSMedrxiv} />
        </div>
      </Card>

      <button
        onClick={handleSave}
        className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold transition-colors"
      >
        💾 Save Scoring Configuration
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Backup sub-tab
// ---------------------------------------------------------------------------
function BackupSettings() {
  const [backups, setBackups] = useState([]);
  const [msg, setMsg] = useState(null);

  const refresh = async () => {
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

  const flash = (text, type = "success") => {
    setMsg({ text, type });
    setTimeout(() => setMsg(null), 4000);
  };

  const handleRestore = async (path) => {
    try {
      await restoreBackup(path);
      flash("Backup restored successfully!");
    } catch (e) {
      flash(e.message, "error");
    }
  };

  const handleCreate = async () => {
    try {
      await createBackup();
      flash("Manual backup created.");
      refresh();
    } catch (e) {
      flash(e.message, "error");
    }
  };

  return (
    <div className="space-y-6">
      <Flash msg={msg} onClear={() => setMsg(null)} />

      <Card title="Available Backups">
        {backups.length === 0 ? (
          <p className="text-sm text-gray-400 py-4 text-center">
            No backups found. Backups are created automatically when you save
            settings.
          </p>
        ) : (
          <div className="divide-y divide-gray-100">
            {backups.map((b, i) => (
              <div
                key={b.path}
                className="flex items-center justify-between py-2.5"
              >
                <span className="text-sm text-gray-700">
                  Backup {i + 1}: {b.date}
                </span>
                <button
                  onClick={() => handleRestore(b.path)}
                  className="px-3 py-1.5 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 rounded-md text-xs font-medium transition-colors"
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
          className="px-5 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
        >
          📁 Create Backup Now
        </button>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Shared helpers / UI atoms
// ---------------------------------------------------------------------------

function Card({ title, desc, children }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
      {desc && <p className="text-xs text-gray-400 mt-0.5 mb-3">{desc}</p>}
      {!desc && <div className="h-3" />}
      {children}
    </div>
  );
}

function NumField({ label, value, onChange, min, max, step = 0.1 }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-600 mb-1">
        {label}
      </label>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        min={min}
        max={max}
        step={step}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
      />
    </div>
  );
}

function Toggle({ label, checked, onChange }) {
  return (
    <label className="flex items-center gap-2 cursor-pointer">
      <input
        type="checkbox"
        checked={checked}
        onChange={() => onChange(!checked)}
        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
      />
      <span className="text-sm text-gray-700">{label}</span>
    </label>
  );
}

function MultiSelect({ label, options, selected, onChange, exclude = [] }) {
  const available = options.filter((o) => !exclude.includes(o));

  const toggle = (item) => {
    if (selected.includes(item)) {
      onChange(selected.filter((s) => s !== item));
    } else {
      onChange([...selected, item]);
    }
  };

  return (
    <div className="mb-3">
      <label className="block text-sm font-medium text-gray-600 mb-1.5">
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
                  ? "bg-indigo-100 text-indigo-700 border-indigo-300"
                  : "bg-gray-50 text-gray-500 border-gray-200 hover:bg-gray-100"
              }`}
            >
              {active && "✓ "}
              {opt}
            </button>
          );
        })}
        {available.length === 0 && (
          <span className="text-xs text-gray-400">No options available</span>
        )}
      </div>
    </div>
  );
}

function Flash({ msg, onClear }) {
  if (!msg) return null;
  return (
    <div
      className={`px-4 py-3 rounded-lg text-sm flex items-center justify-between ${
        msg.type === "error"
          ? "bg-red-50 border border-red-200 text-red-700"
          : "bg-green-50 border border-green-200 text-green-700"
      }`}
    >
      <span>{msg.text}</span>
      <button onClick={onClear} className="ml-2 opacity-50 hover:opacity-100">
        ✕
      </button>
    </div>
  );
}

function lines(text) {
  return text
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
}
