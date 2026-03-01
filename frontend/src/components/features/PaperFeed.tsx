"use client";

import type { Paper, FetchResult, DataSources } from "@/types";
import type { DisplayState } from "@/hooks/useAgentStream";
import PaperCard from "@/components/PaperCard";
import AgentActivityStream from "@/components/features/AgentActivityStream";

interface PaperFeedProps {
  result: FetchResult | null;
  papers: Paper[];
  loading: boolean;
  error: string | null;
  sources: DataSources;
  searchQuery: string;
  onSearchQueryChange: (q: string) => void;
  onExport: () => void;
  archivedTitles: Set<string>;
  onArchive: (paper: Paper) => void;
  displayState: DisplayState;
  isStreaming: boolean;
}

export default function PaperFeed({
  result,
  papers,
  loading,
  error,
  sources,
  searchQuery,
  onSearchQueryChange,
  onExport,
  archivedTitles,
  onArchive,
  displayState,
  isStreaming,
}: PaperFeedProps) {
  const hasActivity = displayState.sources.length > 0 || isStreaming;

  return (
    <div className="flex-1 p-6 space-y-4 min-w-0">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-text-primary">Recent Papers</h2>
        {result && (
          <button
            onClick={onExport}
            className="text-sm text-accent hover:text-accent-hover font-medium"
          >
            Export CSV
          </button>
        )}
      </div>

      {/* SSE activity stream */}
      {hasActivity && (
        <AgentActivityStream
          displayState={displayState}
          isStreaming={isStreaming}
        />
      )}

      {/* Search within results */}
      {result && (
        <div>
          <label htmlFor="results-search" className="sr-only">
            Search within results
          </label>
          <input
            id="results-search"
            type="text"
            placeholder="Search within results…"
            value={searchQuery}
            onChange={(e) => onSearchQueryChange(e.target.value)}
            className="w-full px-4 py-2.5 border border-border bg-surface-raised rounded-lg text-sm text-text-primary placeholder:text-text-muted focus:ring-2 focus:ring-accent focus:border-accent outline-hidden"
          />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* API errors */}
      {result?.errors?.length ? (
        <div className="bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-300 px-4 py-3 rounded-lg text-sm">
          {result.errors.map((e, i) => (
            <div key={i}>{e}</div>
          ))}
        </div>
      ) : null}

      {/* Must-have info */}
      {result?.must_have_keywords?.length ? (
        <div className="bg-accent-subtle border border-accent/20 text-accent-text px-4 py-3 rounded-lg text-sm">
          Must-have filter active: papers must match one of{" "}
          <strong>{result.must_have_keywords.join(", ")}</strong>
        </div>
      ) : null}

      {/* Result count */}
      {result && (
        <p className="text-sm text-text-muted">
          <strong className="text-text-secondary">{papers.length}</strong>{" "}
          papers displayed
          {result.total_before_filter !== result.total_after_filter && (
            <span>
              {" "}
              ({result.total_before_filter - result.total_after_filter} excluded
              by filters)
            </span>
          )}
        </p>
      )}

      {/* Loading — skeleton cards below activity stream */}
      {loading && (
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="bg-surface-raised rounded-xl border border-border p-5 animate-pulse"
            >
              <div className="flex gap-5">
                <div className="flex-1 space-y-3">
                  <div className="h-5 bg-surface-inset rounded w-4/5" />
                  <div className="h-3 bg-surface-inset rounded w-3/5" />
                  <div className="h-3 bg-surface-inset rounded w-2/5" />
                </div>
                <div className="flex flex-col items-center gap-3 w-24">
                  <div className="h-7 w-16 bg-surface-inset rounded-full" />
                  <div className="h-14 w-16 bg-surface-inset rounded-xl" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && !result && !hasActivity && (
        <div className="text-center py-20 text-text-muted">
          <p className="text-4xl mb-3">📄</p>
          <p className="text-lg font-medium">No papers loaded yet</p>
          <p className="text-sm mt-1">
            Configure sources in the sidebar and click{" "}
            <strong>Fetch Papers</strong>.
          </p>
        </div>
      )}

      {/* Papers list */}
      {!loading && papers.length > 0 && (
        <div className="space-y-4">
          {papers.map((paper, idx) => (
            <PaperCard
              key={`${paper.title}-${idx}`}
              paper={paper}
              isArchived={archivedTitles.has(paper.title)}
              onArchive={onArchive}
            />
          ))}
        </div>
      )}

      {/* No results after fetch */}
      {!loading && result && papers.length === 0 && (
        <div className="text-center py-16 text-text-muted">
          <p className="text-4xl mb-3">🔍</p>
          <p className="text-lg font-medium">No papers found</p>
          <p className="text-sm mt-1">
            Try adjusting your keywords or date range in Settings.
          </p>
        </div>
      )}
    </div>
  );
}
