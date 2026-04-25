import { useState, useEffect, useRef, useCallback } from "react";
import { exportPapersCSV, archivePaper, getArchivedPapers } from "@/lib/api";
import type { DataSources, Paper } from "@/types";

const DEFAULT_SOURCES: DataSources = {
  pubmed: true,
  arxiv: false,
  biorxiv: false,
  medrxiv: false,
};

const DEFAULT_SEARCH_MODE = "Brief (PubMed: 1000, Others: 500)";

export function usePaperSearch(defaultSources?: DataSources) {
  const [sources, setSources] = useState<DataSources>(DEFAULT_SOURCES);
  const [searchMode, setSearchMode] = useState(DEFAULT_SEARCH_MODE);
  const [highImpactOnly, setHighImpactOnly] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [archivedTitles, setArchivedTitles] = useState<Set<string>>(new Set());

  // Sync sources once when settings defaults arrive.
  // sourcesReady starts false so the auto-fetch waits until defaultSources
  // has been applied (avoids firing with the stale DEFAULT_SOURCES value).
  const sourcesInitialized = useRef(false);
  const [sourcesReady, setSourcesReady] = useState(false);
  useEffect(() => {
    if (!sourcesInitialized.current && defaultSources !== undefined) {
      sourcesInitialized.current = true;
      setSources(defaultSources);
      setSourcesReady(true);
    }
  }, [defaultSources]);

  // Load archived titles on mount
  useEffect(() => {
    getArchivedPapers()
      .then((data) => setArchivedTitles(new Set(data.archived_titles)))
      .catch((err) => console.error("Failed to load archived papers:", err));
  }, []);

  const exportCSV = useCallback(async () => {
    try {
      const blob = await exportPapersCSV(sources, searchMode);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `papers_${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error("Export failed:", e);
    }
  }, [sources, searchMode]);

  const archive = useCallback(async (paper: Paper) => {
    try {
      await archivePaper(paper);
      setArchivedTitles((prev) => new Set(prev).add(paper.title));
    } catch (e) {
      console.error("Archive failed:", e);
    }
  }, []);

  const toggleSource = useCallback((key: keyof DataSources) => {
    setSources((prev) => ({ ...prev, [key]: !prev[key] }));
  }, []);

  // Explicitly reset sources when switching model slots, bypassing the
  // "initialize once" guard so the new slot's defaults take effect.
  const resetSources = useCallback((newSources: DataSources) => {
    setSources(newSources);
    setSourcesReady(true);
  }, []);

  return {
    sources,
    sourcesReady,
    searchMode,
    highImpactOnly,
    searchQuery,
    archivedTitles,
    setSearchMode,
    setHighImpactOnly,
    setSearchQuery,
    toggleSource,
    resetSources,
    exportCSV,
    archive,
  };
}
