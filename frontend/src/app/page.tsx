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

export default function PapersPage() {
  const { settings } = useSettings();
  const keywords = settings?.keywords || [];
  const search = usePaperSearch(settings?.search_settings?.default_sources);
  const stream = useAgentStream();
  const [mode, setMode] = useState<"classic" | "agent">("classic");

  // Auto-fetch once when keywords become available
  const didAutoFetch = useRef(false);
  useEffect(() => {
    if (!didAutoFetch.current && keywords.length > 0) {
      didAutoFetch.current = true;
      stream.startStream(search.sources, search.searchMode);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [keywords.length]);

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

  if (!settings) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Spinner size="lg" />
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
      />

      <DashboardPanel
        papers={activePapers}
        allPapers={stream.result?.papers || []}
        loading={stream.isStreaming}
      />
    </div>
  );
}
