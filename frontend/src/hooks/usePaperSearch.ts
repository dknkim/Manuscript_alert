import { useState, useEffect, useRef, useCallback } from "react";
import { exportPapersCSV, archivePaper, getArchivedPapers } from "@/lib/api";
import type { DataSources, Paper } from "@/types";

const ALL_SOURCES: DataSources = {
  arxiv: true,
  biorxiv: true,
  medrxiv: true,
  pubmed: true,
};

const DEFAULT_SEARCH_MODE = "Brief (PubMed: 1000, Others: 500)";

export function usePaperSearch(defaultSources?: DataSources) {
  const [sources, setSources] = useState<DataSources>(ALL_SOURCES);
  const [searchMode, setSearchMode] = useState(DEFAULT_SEARCH_MODE);
  const [highImpactOnly, setHighImpactOnly] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [archivedTitles, setArchivedTitles] = useState<Set<string>>(new Set());

  // Sync sources once when settings defaults arrive
  const sourcesInitialized = useRef(false);
  useEffect(() => {
    if (!sourcesInitialized.current && defaultSources) {
      sourcesInitialized.current = true;
      setSources(defaultSources);
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

  return {
    sources,
    searchMode,
    highImpactOnly,
    searchQuery,
    archivedTitles,
    setSearchMode,
    setHighImpactOnly,
    setSearchQuery,
    toggleSource,
    exportCSV,
    archive,
  };
}
