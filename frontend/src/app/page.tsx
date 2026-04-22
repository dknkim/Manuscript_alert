"use client";

import { useState, useEffect, useRef, useMemo } from "react";
import { useSettings } from "@/hooks/useSettings";
import { usePaperSearch } from "@/hooks/usePaperSearch";
import { useAgentStream } from "@/hooks/useAgentStream";
import SearchPanel from "@/components/features/SearchPanel";
import PaperFeed from "@/components/features/PaperFeed";
import DashboardPanel from "@/components/features/DashboardPanel";
import Spinner from "@/components/ui/Spinner";
import type { Paper } from "@/types";

const AUTO_RETRY_SECONDS = 20;

export default function PapersPage() {
  const { settings, loading, error, warmingUp, reload } = useSettings();
  const [retryCountdown, setRetryCountdown] = useState(0);
  const keywords = settings?.keywords || [];
  const settingsSignature = useMemo(
    () => JSON.stringify(settings ?? null),
    [settings],
  );
  // Resolve to undefined while settings are loading, then always a defined value.
  // This ensures usePaperSearch knows when settings have actually arrived.
  const defaultSources = settings
    ? (settings.search_settings?.default_sources ?? { pubmed: true, arxiv: false, biorxiv: false, medrxiv: false })
    : undefined;
  const search = usePaperSearch(defaultSources);
  const stream = useAgentStream(settings ? settingsSignature : undefined);
  const [mode, setMode] = useState<"classic" | "agent">("classic");

  // Delay spinner to avoid flash on fast loads
  const [showSpinner, setShowSpinner] = useState(false);
  useEffect(() => {
    if (!loading) { setShowSpinner(false); return; }
    const t = window.setTimeout(() => setShowSpinner(true), 500);
    return () => window.clearTimeout(t);
  }, [loading]);

  // Show waking message in PaperFeed after 5s of streaming
  const [serverWakingUp, setServerWakingUp] = useState(false);
  useEffect(() => {
    if (!stream.isStreaming) { setServerWakingUp(false); return; }
    const t = window.setTimeout(() => setServerWakingUp(true), 5000);
    return () => window.clearTimeout(t);
  }, [stream.isStreaming]);

  // Auto-retry when error is shown
  useEffect(() => {
    if (!error) { setRetryCountdown(0); return; }
    setRetryCountdown(AUTO_RETRY_SECONDS);
    const interval = setInterval(() => {
      setRetryCountdown((prev) => {
        if (prev <= 1) { clearInterval(interval); void reload(); return 0; }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [error]);

  // Auto-fetch once when both keywords and sources are ready
  const didAutoFetch = useRef(false);
  useEffect(() => {
    if (
      !didAutoFetch.current &&
      keywords.length > 0 &&
      search.sourcesReady &&
      !stream.result
    ) {
      didAutoFetch.current = true;
      stream.startStream(search.sources, search.searchMode);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [keywords.length, search.sourcesReady, stream.result]);

  const handleFetch = () => {
    stream.startStream(search.sources, search.searchMode);
  };

  const activePapers = useMemo(() => {
    const papers: Paper[] = stream.result?.papers || [];
    let filtered = papers;
    if (search.highImpactOnly) {
      filtered = filtered.filter((p) => p.is_high_impact);
    }
    if (search.searchQuery.trim()) {
      const q = search.searchQuery.toLowerCase();
      filtered = filtered.filter(
        (p) =>
          p.title.toLowerCase().includes(q) ||
          p.abstract.toLowerCase().includes(q) ||
          p.authors.toLowerCase().includes(q),
      );
    }
    return filtered;
  }, [stream.result, search.highImpactOnly, search.searchQuery]);

  if (loading && !settings) {
    if (!showSpinner) return null;
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] px-6">
        <div className="max-w-md w-full rounded-xl border border-border bg-surface-raised p-6 text-center">
          <h2 className="text-lg font-semibold text-text-primary">
            Failed to load settings
          </h2>
          <p className="mt-2 text-sm text-text-muted">
            {error || "The API did not return settings in time."}
          </p>
          <p className="mt-1 text-xs text-text-muted">
            {retryCountdown > 0
              ? `Retrying automatically in ${retryCountdown}s…`
              : "Retrying…"}
          </p>
          <button
            onClick={() => { setRetryCountdown(0); void reload(); }}
            className="mt-4 inline-flex items-center justify-center rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-accent-hover"
          >
            Retry Now
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex">
      <SearchPanel
        sources={search.sources}
        searchMode={search.searchMode}
        highImpactOnly={search.highImpactOnly}
        loading={stream.isStreaming}
        keywords={keywords}
        mode={mode}
        onSourceToggle={search.toggleSource}
        onSearchModeChange={search.setSearchMode}
        onHighImpactChange={search.setHighImpactOnly}
        onModeChange={setMode}
        onFetch={handleFetch}
      />

      <PaperFeed
        result={stream.result}
        papers={activePapers}
        loading={stream.isStreaming}
        error={stream.error}
        sources={search.sources}
        searchQuery={search.searchQuery}
        onSearchQueryChange={search.setSearchQuery}
        onExport={search.exportCSV}
        archivedTitles={search.archivedTitles}
        onArchive={search.archive}
        displayState={stream.displayState}
        isStreaming={stream.isStreaming}
        serverWakingUp={serverWakingUp}
      />

      <DashboardPanel
        papers={activePapers}
        allPapers={stream.result?.papers || []}
        loading={stream.isStreaming}
        highImpactOnly={search.highImpactOnly}
        onHighImpactChange={search.setHighImpactOnly}
      />
    </div>
  );
}
