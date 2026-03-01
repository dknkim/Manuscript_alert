"use client";

import type { DataSources } from "@/types";
import ModeSwitch from "@/components/ui/ModeSwitch";

interface SearchMode {
  value: string;
  label: string;
  hint: string;
}

const SEARCH_MODES: SearchMode[] = [
  {
    value: "Brief (PubMed: 1000, Others: 500)",
    label: "Brief",
    hint: "Fastest results with recent papers.",
  },
  {
    value: "Standard (PubMed: 2500, Others: 1000)",
    label: "Standard",
    hint: "Balanced for speed and coverage.",
  },
  {
    value: "Extended (All sources: 5000)",
    label: "Extended",
    hint: "May take 2-3x longer but comprehensive.",
  },
];

interface SearchPanelProps {
  sources: DataSources;
  searchMode: string;
  highImpactOnly: boolean;
  loading: boolean;
  keywords: string[];
  mode: "classic" | "agent";
  onSourceToggle: (key: keyof DataSources) => void;
  onSearchModeChange: (mode: string) => void;
  onHighImpactChange: (v: boolean) => void;
  onModeChange: (mode: "classic" | "agent") => void;
  onFetch: () => void;
}

export default function SearchPanel({
  sources,
  searchMode,
  highImpactOnly,
  loading,
  keywords,
  mode,
  onSourceToggle,
  onSearchModeChange,
  onHighImpactChange,
  onModeChange,
  onFetch,
}: SearchPanelProps) {
  return (
    <aside className="w-72 shrink-0 bg-surface-raised border-r border-border p-5 space-y-6 sticky top-[73px] h-[calc(100vh-73px)] overflow-y-auto">
      {/* Mode switch */}
      <div>
        <h3 className="text-xs font-semibold text-text-muted uppercase mb-2">
          Search Mode
        </h3>
        <ModeSwitch mode={mode} onChange={onModeChange} />
      </div>

      {/* Fetch button — primary action, top position */}
      <button
        onClick={onFetch}
        disabled={loading}
        className="w-full py-2.5 bg-accent hover:bg-accent-hover disabled:opacity-50 text-white rounded-lg text-sm font-semibold transition-colors flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
            Fetching…
          </>
        ) : (
          "Fetch Papers"
        )}
      </button>

      {/* Data Sources — most frequently changed */}
      <div>
        <h3 className="text-xs font-semibold text-text-muted uppercase mb-2">
          Data Sources
        </h3>
        <div className="grid grid-cols-2 gap-2">
          {(
            [
              { key: "arxiv", label: "arXiv" },
              { key: "biorxiv", label: "bioRxiv" },
              { key: "medrxiv", label: "medRxiv" },
              { key: "pubmed", label: "PubMed" },
            ] as const
          ).map((s) => (
            <label
              key={s.key}
              className="flex items-center gap-2 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={sources[s.key]}
                onChange={() => onSourceToggle(s.key)}
                className="rounded border-border text-accent focus:ring-accent"
              />
              <span className="text-sm text-text-secondary">{s.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Search Limits — moderately changed */}
      <div>
        <h3 className="text-xs font-semibold text-text-muted uppercase mb-2">
          Search Limits
        </h3>
        <div className="space-y-2">
          {SEARCH_MODES.map((m) => (
            <label
              key={m.value}
              className="flex items-start gap-2 cursor-pointer"
            >
              <input
                type="radio"
                name="searchMode"
                value={m.value}
                checked={searchMode === m.value}
                onChange={() => onSearchModeChange(m.value)}
                className="mt-0.5 text-accent focus:ring-accent"
              />
              <div>
                <span className="text-sm font-medium text-text-secondary">
                  {m.label}
                </span>
                <p className="text-xs text-text-muted">{m.hint}</p>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Journal Quality — rarely changed */}
      <div>
        <h3 className="text-xs font-semibold text-text-muted uppercase mb-2">
          Journal Quality
        </h3>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={highImpactOnly}
            onChange={() => onHighImpactChange(!highImpactOnly)}
            className="rounded border-border text-accent focus:ring-accent"
          />
          <span className="text-sm text-text-secondary">
            Relevant Journals Only
          </span>
        </label>
      </div>

      {/* Keywords preview — informational only */}
      <div>
        <h3 className="text-xs font-semibold text-text-muted uppercase mb-2">
          Active Keywords ({keywords.length})
        </h3>
        <div className="flex flex-wrap gap-1">
          {keywords.slice(0, 12).map((kw) => (
            <span
              key={kw}
              className="text-xs px-2 py-0.5 bg-surface-inset rounded-full text-text-secondary"
            >
              {kw}
            </span>
          ))}
          {keywords.length > 12 && (
            <span className="text-xs text-text-muted">
              +{keywords.length - 12} more
            </span>
          )}
        </div>
      </div>
    </aside>
  );
}
