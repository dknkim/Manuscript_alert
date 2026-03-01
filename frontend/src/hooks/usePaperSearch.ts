import { useState, useEffect, useRef, useMemo, useCallback } from "react";
import {
  fetchPapers,
  exportPapersCSV,
  archivePaper,
  getArchivedPapers,
} from "@/lib/api";
import type { FetchResult, DataSources, Paper } from "@/types";

const ALL_SOURCES: DataSources = {
  arxiv: true,
  biorxiv: true,
  medrxiv: true,
  pubmed: true,
};

const DEFAULT_SEARCH_MODE = "Brief (PubMed: 1000, Others: 500)";

export function usePaperSearch(
  keywords: string[],
  defaultSources?: DataSources,
) {
  const [result, setResult] = useState<FetchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
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

  const fetch = useCallback(
    async (overrideSources?: DataSources) => {
      const srcs = overrideSources || sources;
      if (!Object.values(srcs).some(Boolean)) {
        setError("Please select at least one data source.");
        return;
      }
      if (keywords.length === 0) {
        setError("No keywords configured. Add keywords in Settings.");
        return;
      }
      setLoading(true);
      setError(null);
      try {
        setResult(await fetchPapers(srcs, searchMode));
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    },
    [sources, searchMode, keywords],
  );

  // Auto-fetch on first load using current sources
  const didAutoFetch = useRef(false);
  useEffect(() => {
    if (!didAutoFetch.current && keywords.length > 0 && !result) {
      didAutoFetch.current = true;
      fetch();
    }
  }, [keywords, fetch, result]);

  const filteredPapers = useMemo(() => {
    if (!result) return [];
    let papers = result.papers || [];
    if (highImpactOnly) papers = papers.filter((p) => p.is_high_impact);
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      papers = papers.filter(
        (p) =>
          p.title.toLowerCase().includes(q) ||
          p.abstract.toLowerCase().includes(q) ||
          p.authors.toLowerCase().includes(q),
      );
    }
    return papers;
  }, [result, highImpactOnly, searchQuery]);

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
    result,
    filteredPapers,
    loading,
    error,
    sources,
    searchMode,
    highImpactOnly,
    searchQuery,
    archivedTitles,
    setSearchMode,
    setHighImpactOnly,
    setSearchQuery,
    toggleSource,
    fetch,
    exportCSV,
    archive,
  };
}
