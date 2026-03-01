"use client";

import { useState } from "react";
import type { Paper } from "@/types";

interface StatisticsProps {
  papers: Paper[];
  allPapers: Paper[];
}

export default function Statistics({ papers, allPapers }: StatisticsProps) {
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
  const topKeywords = Object.entries(kwCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);

  // Avg + max score
  const scores = allPapers.map((p) => p.relevance_score);
  const avg = (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1);
  const max = Math.max(...scores).toFixed(1);

  return (
    <div className="space-y-5">
      <Section title="Overview" defaultOpen>
        <Metric label="Total Papers" value={allPapers.length} />
        <Metric label="Avg Score" value={avg} />
        <Metric label="Max Score" value={max} />
      </Section>

      <Section title="Sources" defaultOpen>
        {Object.entries(sourceCounts).map(([src, count]) => (
          <div key={src} className="flex justify-between text-sm py-0.5">
            <span className="font-medium text-text-secondary">{src}</span>
            <span className="text-text-muted">{count}</span>
          </div>
        ))}
      </Section>

      {highImpact > 0 && (
        <Section title="Journal Quality" defaultOpen>
          <Metric label="Relevant Journals" value={highImpact} />
        </Section>
      )}

      <Section title="Top Keywords">
        {topKeywords.map(([kw, count]) => (
          <div key={kw} className="flex justify-between text-sm py-0.5">
            <span className="font-medium text-text-secondary">{kw}</span>
            <span className="text-text-muted">{count}</span>
          </div>
        ))}
      </Section>
    </div>
  );
}

/* ── Sub-components ──────────────────────────────────────── */

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

function Section({
  title,
  defaultOpen = false,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState<boolean>(defaultOpen);
  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-2.5 bg-surface-inset hover:bg-surface transition-colors"
      >
        <span className="text-sm font-semibold text-text-secondary">
          {title}
        </span>
        <svg
          className={`w-4 h-4 text-text-muted transition-transform ${
            open ? "rotate-180" : ""
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>
      {open && <div className="px-4 py-3">{children}</div>}
    </div>
  );
}
