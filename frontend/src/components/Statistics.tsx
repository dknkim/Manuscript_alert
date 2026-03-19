"use client";

import { useState } from "react";
import type { Paper } from "@/types";

interface StatisticsProps {
  papers: Paper[];
  allPapers: Paper[];
}

const KEYWORDS_VISIBLE = 8;

export default function Statistics({ papers, allPapers }: StatisticsProps) {
  const [showAllKeywords, setShowAllKeywords] = useState(false);

  if (!allPapers || allPapers.length === 0) return null;

  // Source counts
  const sourceCounts: Record<string, number> = {};
  allPapers.forEach((p) => {
    sourceCounts[p.source] = (sourceCounts[p.source] || 0) + 1;
  });

  // High-impact count
  const highImpact = allPapers.filter((p) => p.is_high_impact).length;

  // Keyword frequency
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

  // Avg + max score
  const scores = allPapers.map((p) => p.relevance_score);
  const avg = (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1);
  const max = Math.max(...scores).toFixed(1);

  return (
    <div className="space-y-4">
      {/* Score Summary */}
      <div>
        <SectionHeader>Score Summary</SectionHeader>
        <Metric label="Total Papers" value={allPapers.length} />
        <Metric label="Avg Score" value={avg} />
        <Metric label="Max Score" value={max} />
        {highImpact > 0 && (
          <div className="flex justify-between items-baseline py-1 mt-1 border-t border-border/50 pt-2">
            <span className="text-sm text-text-muted">Relevant Journals</span>
            <span className="text-xl font-bold text-amber-500 dark:text-amber-400">{highImpact}</span>
          </div>
        )}
      </div>

      {/* Top Keywords */}
      {allKeywords.length > 0 && (
        <div className="border-t border-border pt-4">
          <SectionHeader>Top Keywords</SectionHeader>
          {visibleKeywords.map(([kw, count]) => (
            <div key={kw} className="flex justify-between text-sm py-0.5">
              <span className="font-medium text-text-secondary">{kw}</span>
              <span className="text-text-muted">{count}</span>
            </div>
          ))}
          {hasMoreKeywords && (
            <button
              onClick={() => setShowAllKeywords(!showAllKeywords)}
              className="text-xs text-accent hover:text-accent-hover mt-1"
            >
              {showAllKeywords
                ? "show less"
                : `show all (${allKeywords.length})`}
            </button>
          )}
        </div>
      )}

      {/* Sources */}
      <div className="border-t border-border pt-4">
        <SectionHeader>Sources</SectionHeader>
        {Object.entries(sourceCounts).map(([src, count]) => (
          <div key={src} className="flex justify-between text-sm py-0.5">
            <span className="font-medium text-text-secondary">{src}</span>
            <span className="text-text-muted">{count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Sub-components ──────────────────────────────────────── */

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="text-[11px] uppercase tracking-wide text-text-muted mb-2">
      {children}
    </h3>
  );
}

function Metric({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="flex justify-between items-baseline py-1">
      <span className="text-sm text-text-muted">{label}</span>
      <span className="text-xl font-bold text-text-primary">{value}</span>
    </div>
  );
}
