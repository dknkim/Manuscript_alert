"use client";

import { useEffect, useState, useCallback } from "react";
import { BookOpen, BookmarkX, ExternalLink, RefreshCw } from "lucide-react";
import { getArchivedPapers, unarchivePaper } from "@/lib/api";
import type { Paper, ArchiveResponse } from "@/types";
import Spinner from "@/components/ui/Spinner";

const RETRY_DELAYS_MS = [3000, 6000, 12000, 20000];
const TIMEOUT_MS = 20000;

async function fetchWithRetry(): Promise<ArchiveResponse> {
  for (let attempt = 0; attempt <= RETRY_DELAYS_MS.length; attempt++) {
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
      try {
        const res = await getArchivedPapers();
        clearTimeout(timer);
        return res;
      } finally {
        clearTimeout(timer);
      }
    } catch (err) {
      if (attempt < RETRY_DELAYS_MS.length) {
        await new Promise((resolve) =>
          window.setTimeout(resolve, RETRY_DELAYS_MS[attempt]),
        );
        continue;
      }
      throw err;
    }
  }
  throw new Error("Failed to load archive");
}

export default function KnowledgeBasePage() {
  const [data, setData] = useState<ArchiveResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [warmingUp, setWarmingUp] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [removing, setRemoving] = useState<Set<string>>(new Set());

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    setWarmingUp(false);

    // Optimistically try once; if it fails, show warming-up and retry
    try {
      const res = await getArchivedPapers();
      setData(res);
      setLoading(false);
      return;
    } catch {
      setWarmingUp(true);
    }

    try {
      const res = await fetchWithRetry();
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load archive");
    } finally {
      setLoading(false);
      setWarmingUp(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const handleUnarchive = async (paper: Paper, date: string) => {
    setRemoving((prev) => new Set(prev).add(paper.title));
    try {
      await unarchivePaper(paper.title, date);
      setData((prev) => {
        if (!prev) return prev;
        const updated = { ...prev.archive };
        updated[date] = (updated[date] ?? []).filter(
          (p) => p.title !== paper.title,
        );
        if (updated[date].length === 0) delete updated[date];
        return {
          ...prev,
          archive: updated,
          archived_titles: prev.archived_titles.filter(
            (t) => t !== paper.title,
          ),
          total: prev.total - 1,
        };
      });
    } finally {
      setRemoving((prev) => {
        const next = new Set(prev);
        next.delete(paper.title);
        return next;
      });
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
        <Spinner size="lg" />
        <p className="text-sm text-text-muted animate-pulse">
          {warmingUp ? "Server is waking up, please wait…" : "Loading archived papers…"}
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6 flex flex-col items-center gap-4 py-20">
        <p className="text-sm text-text-muted">{error}</p>
        <button
          onClick={load}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-surface-raised border border-border text-text-secondary hover:text-text-primary transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
          Retry
        </button>
      </div>
    );
  }

  const dates = data ? Object.keys(data.archive).sort((a, b) => b.localeCompare(a)) : [];
  const isEmpty = dates.length === 0;

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            Knowledge Base
          </h2>
          {data && data.total > 0 && (
            <p className="text-sm text-text-muted mt-0.5">
              {data.total} archived {data.total === 1 ? "paper" : "papers"}
            </p>
          )}
        </div>
        {data && (
          <button
            onClick={load}
            className="p-2 rounded-md text-text-secondary hover:text-text-primary hover:bg-surface-inset transition-colors"
            title="Refresh"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        )}
      </div>

      {isEmpty ? (
        <div className="text-center py-20 text-text-muted">
          <BookOpen className="h-16 w-16 mx-auto mb-4 opacity-40" />
          <p className="text-lg font-medium">No archived papers yet</p>
          <p className="text-sm mt-1">
            Use the <strong>Archive</strong> button on any paper to save it here.
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {dates.map((date) => (
            <section key={date}>
              <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-3">
                {date}
              </h3>
              <div className="space-y-3">
                {data!.archive[date].map((paper) => (
                  <div
                    key={paper.title}
                    className="bg-surface-raised rounded-xl border border-border p-5"
                  >
                    <div className="flex gap-4">
                      <div className="flex-1 min-w-0">
                        <a
                          href={paper.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm font-semibold text-text-primary hover:text-accent leading-snug flex items-start gap-1 group"
                        >
                          <span className="line-clamp-2">{paper.title}</span>
                          <ExternalLink className="h-3.5 w-3.5 shrink-0 mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </a>
                        <p className="text-xs text-text-muted mt-1 truncate">
                          {paper.authors}
                        </p>
                        {paper.abstract && (
                          <p className="text-xs text-text-secondary mt-2 line-clamp-2">
                            {paper.abstract}
                          </p>
                        )}
                        {paper.matched_keywords?.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {paper.matched_keywords.map((kw) => (
                              <span
                                key={kw}
                                className="px-1.5 py-0.5 rounded text-[10px] bg-accent-subtle text-accent-text"
                              >
                                {kw}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="flex flex-col items-center gap-2 shrink-0">
                        <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-surface-inset text-text-secondary capitalize">
                          {paper.source}
                        </span>
                        <span className="text-xs font-bold text-text-secondary">
                          {Math.round(paper.relevance_score)}
                        </span>
                        <button
                          onClick={() => handleUnarchive(paper, date)}
                          disabled={removing.has(paper.title)}
                          className="mt-1 px-2 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 bg-surface-inset text-text-secondary hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950 dark:hover:text-red-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                          title="Remove from archive"
                        >
                          <BookmarkX className="size-3.5" />
                          Remove
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
