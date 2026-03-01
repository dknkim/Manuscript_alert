"use client";

import type { Paper } from "@/types";
import Statistics from "@/components/Statistics";

interface DashboardPanelProps {
  papers: Paper[];
  allPapers: Paper[];
  loading: boolean;
}

function StatsSkeleton() {
  return (
    <div className="p-5 space-y-6 animate-pulse">
      <div className="h-4 bg-surface-inset rounded w-24" />
      {/* Overview skeleton */}
      <div className="space-y-3">
        <div className="h-4 bg-surface-inset rounded w-20" />
        <div className="flex justify-between">
          <div className="h-3 bg-surface-inset rounded w-24" />
          <div className="h-5 bg-surface-inset rounded w-10" />
        </div>
        <div className="flex justify-between">
          <div className="h-3 bg-surface-inset rounded w-20" />
          <div className="h-5 bg-surface-inset rounded w-10" />
        </div>
        <div className="flex justify-between">
          <div className="h-3 bg-surface-inset rounded w-20" />
          <div className="h-5 bg-surface-inset rounded w-10" />
        </div>
      </div>
      {/* Sources skeleton */}
      <div className="space-y-3">
        <div className="h-4 bg-surface-inset rounded w-16" />
        <div className="flex justify-between">
          <div className="h-3 bg-surface-inset rounded w-16" />
          <div className="h-4 bg-surface-inset rounded w-8" />
        </div>
        <div className="flex justify-between">
          <div className="h-3 bg-surface-inset rounded w-12" />
          <div className="h-4 bg-surface-inset rounded w-8" />
        </div>
        <div className="flex justify-between">
          <div className="h-3 bg-surface-inset rounded w-14" />
          <div className="h-4 bg-surface-inset rounded w-8" />
        </div>
      </div>
      {/* Journal Quality skeleton */}
      <div className="space-y-3">
        <div className="h-4 bg-surface-inset rounded w-28" />
        <div className="flex justify-between">
          <div className="h-3 bg-surface-inset rounded w-28" />
          <div className="h-5 bg-surface-inset rounded w-8" />
        </div>
      </div>
    </div>
  );
}

export default function DashboardPanel({
  papers,
  allPapers,
  loading,
}: DashboardPanelProps) {
  const hasData = allPapers.length > 0;

  return (
    <aside className="w-72 shrink-0 border-l border-border bg-surface-raised sticky top-[73px] h-[calc(100vh-73px)] overflow-y-auto">
      {loading && !hasData ? (
        <StatsSkeleton />
      ) : hasData ? (
        <div className="p-5">
          <h2 className="text-sm font-semibold text-text-primary uppercase tracking-wider mb-4">
            Statistics
          </h2>
          <Statistics papers={papers} allPapers={allPapers} />
        </div>
      ) : (
        <div className="p-5 text-center text-text-muted">
          <p className="text-sm mt-8">
            Run a search to see statistics here.
          </p>
        </div>
      )}
    </aside>
  );
}
