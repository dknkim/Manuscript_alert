"use client";

import { useState } from "react";
import type { Paper } from "@/types";

interface StatisticsProps {
  papers: Paper[];
  allPapers: Paper[];
  highImpactOnly?: boolean;
  onHighImpactChange?: (value: boolean) => void;
}

const KEYWORDS_VISIBLE = 8;

export default function Statistics({
  papers,
  allPapers,
  highImpactOnly,
  onHighImpactChange,
}: StatisticsProps) {
  const [showAllKeywords, setShowAllKeywords] = useState(false);

  if (!allPapers || allPapers.length === 0) return null;

  // --- Derived data ---

  // High-impact count is always from the full set (it's the filter criterion)
  const highImpact = allPapers.filter((p) => p.is_high_impact).length;

  // Source breakdown reflects the active view:
  // when the filter is on, show how the filtered subset breaks down by source
  const sourceBase = highImpactOnly ? papers : allPapers;
  const sourceCounts: Record<string, number> = {};
  sourceBase.forEach((p) => {
    sourceCounts[p.source] = (sourceCounts[p.source] || 0) + 1;
  });
  const sourceEntries = Object.entries(sourceCounts).sort((a, b) => b[1] - a[1]);

  // Keyword frequency always from the full set (diagnostic, not filtered)
  const kwCounts: Record<string, number> = {};
  allPapers.forEach((p) => {
    (p.matched_keywords || []).forEach((kw) => {
      kwCounts[kw] = (kwCounts[kw] || 0) + 1;
    });
  });
  const allKeywords = Object.entries(kwCounts).sort((a, b) => b[1] - a[1]);
  const visibleKeywords = showAllKeywords
    ? allKeywords
    : allKeywords.slice(0, KEYWORDS_VISIBLE);
  const hasMoreKeywords = allKeywords.length > KEYWORDS_VISIBLE;

  // Scores always from the full set
  const scores = allPapers.map((p) => p.relevance_score);
  const avg = (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1);
  const max = Math.max(...scores).toFixed(1);

  return (
    <div className="space-y-5">

      {/* ── Section 1: Filters (Relevant Journals + Sources) ─────── */}
      {highImpact > 0 && (
        <div>
          <SectionHeader>Filters</SectionHeader>

          {/* Relevant Journals toggle */}
          <button
            onClick={() => onHighImpactChange?.(!highImpactOnly)}
            aria-pressed={highImpactOnly}
            className={[
              "flex justify-between items-center w-full rounded-md px-2.5 py-2 mb-2",
              "cursor-pointer transition-all duration-150",
              "text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
              highImpactOnly
                ? "bg-amber-100 dark:bg-amber-900/40 ring-1 ring-amber-400 dark:ring-amber-600"
                : "bg-amber-50 dark:bg-amber-950/30 ring-1 ring-amber-200/60 dark:ring-amber-800/40 hover:bg-amber-100/80 dark:hover:bg-amber-900/30 hover:ring-amber-300 dark:hover:ring-amber-700",
            ].join(" ")}
          >
            <div className="flex items-center gap-2">
              {/* Active indicator dot */}
              <span
                className={[
                  "w-1.5 h-1.5 rounded-full shrink-0 transition-colors duration-150",
                  highImpactOnly
                    ? "bg-amber-500 dark:bg-amber-400"
                    : "bg-amber-300 dark:bg-amber-700",
                ].join(" ")}
              />
              <span
                className={[
                  "text-sm transition-colors duration-150",
                  highImpactOnly
                    ? "font-medium text-amber-900 dark:text-amber-200"
                    : "font-normal text-text-secondary",
                ].join(" ")}
              >
                Relevant Journals
              </span>
            </div>
            {/* Count badge */}
            <span
              className={[
                "text-xs font-semibold px-1.5 py-0.5 rounded transition-colors duration-150",
                highImpactOnly
                  ? "bg-amber-500 dark:bg-amber-400 text-white dark:text-amber-950"
                  : "bg-amber-200/70 dark:bg-amber-800/60 text-amber-800 dark:text-amber-300",
              ].join(" ")}
            >
              {highImpact}
            </span>
          </button>

          {/* Sources — contextually linked to the toggle above */}
          <div
            className={[
              "rounded-md px-2.5 py-2 transition-all duration-200",
              highImpactOnly
                ? "bg-surface-inset border-l-2 border-amber-400 dark:border-amber-600"
                : "bg-transparent border-l-2 border-transparent",
            ].join(" ")}
          >
            <div className="flex items-baseline justify-between mb-1.5">
              <span className="text-[11px] font-semibold uppercase tracking-wide text-text-secondary">
                Sources
              </span>
              {highImpactOnly && (
                <span className="text-[10px] text-amber-600 dark:text-amber-400 font-medium">
                  filtered
                </span>
              )}
            </div>
            {sourceEntries.map(([src, count]) => (
              <div key={src} className="flex justify-between items-baseline py-0.5">
                <span className="text-sm text-text-secondary">{src}</span>
                <span className="text-sm font-medium text-text-secondary">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Section 2: Score Summary ──────────────────────────────── */}
      <div className={highImpact > 0 ? "border-t border-border pt-5" : ""}>
        <SectionHeader>Score Summary</SectionHeader>
        <Metric label="Total Papers" value={allPapers.length} />
        <Metric label="Avg Score" value={avg} />
        <Metric label="Max Score" value={max} />
      </div>

      {/* ── Section 3: Top Keywords ───────────────────────────────── */}
      {allKeywords.length > 0 && (
        <div className="border-t border-border pt-5">
          <SectionHeader>Top Keywords</SectionHeader>
          <div className="space-y-0.5">
            {visibleKeywords.map(([kw, count]) => (
              <div key={kw} className="flex justify-between items-baseline py-0.5">
                <span className="text-xs font-medium text-text-secondary">{kw}</span>
                <span className="text-xs text-text-muted">{count}</span>
              </div>
            ))}
          </div>
          {hasMoreKeywords && (
            <button
              onClick={() => setShowAllKeywords(!showAllKeywords)}
              className="text-xs text-accent hover:text-accent-hover mt-2 transition-colors duration-100"
            >
              {showAllKeywords
                ? "show less"
                : `show all (${allKeywords.length})`}
            </button>
          )}
        </div>
      )}

    </div>
  );
}

/* ── Sub-components ─────────────────────────────────────────── */

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="text-[11px] font-semibold uppercase tracking-wide text-text-secondary mb-2">
      {children}
    </h3>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex justify-between items-baseline py-1">
      <span className="text-sm text-text-secondary">{label}</span>
      <span className="text-xl font-bold text-text-primary">{value}</span>
    </div>
  );
}
