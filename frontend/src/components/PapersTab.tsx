"use client";

import {
  useState,
  useEffect,
  useRef,
  useMemo,
  useCallback,
  type Dispatch,
  type SetStateAction,
} from "react";
import { fetchPapers, exportPapersCSV, archivePaper } from "@/lib/api";
import type { Settings, FetchResult, DataSources, Paper } from "@/types";
import SearchPanel from "@/components/features/SearchPanel";
import PaperFeed from "@/components/features/PaperFeed";
import DashboardPanel from "@/components/features/DashboardPanel";

interface PapersTabProps {
  settings: Settings;
  result: FetchResult | null;
  setResult: Dispatch<SetStateAction<FetchResult | null>>;
  loading: boolean;
  setLoading: Dispatch<SetStateAction<boolean>>;
  error: string | null;
  setError: Dispatch<SetStateAction<string | null>>;
  archivedTitles: Set<string>;
  setArchivedTitles: Dispatch<SetStateAction<Set<string>>>;
}

export default function PapersTab({
  settings,
  result,
  setResult,
  loading,
  setLoading,
  error,
  setError,
  archivedTitles,
  setArchivedTitles,
}: PapersTabProps) {
  const keywords: string[] = settings.keywords || [];

  const [sources, setSources] = useState<DataSources>({
    arxiv: true,
    biorxiv: true,
    medrxiv: true,
    pubmed: true,
  });
  const [searchMode, setSearchMode] = useState<string>(
    "Brief (PubMed: 1000, Others: 500)",
  );
  const [highImpactOnly, setHighImpactOnly] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [mode, setMode] = useState<"classic" | "agent">("classic");

  // ---------- fetch ----------
  const handleFetch = useCallback(
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
        const data = await fetchPapers(srcs, searchMode);
        setResult(data);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    },
    [sources, searchMode, keywords, setResult, setLoading, setError],
  );

  // ---------- auto-fetch on first load ----------
  const didAutoFetch = useRef(false);
  useEffect(() => {
    if (!didAutoFetch.current && keywords.length > 0 && !result) {
      didAutoFetch.current = true;
      handleFetch({
        arxiv: true,
        biorxiv: true,
        medrxiv: true,
        pubmed: true,
      });
    }
  }, [keywords, handleFetch, result]);

  // ---------- filter locally ----------
  const filteredPapers = useMemo(() => {
    if (!result) return [];
    let papers = result.papers || [];
    if (highImpactOnly) {
      papers = papers.filter((p) => p.is_high_impact);
    }
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

  // ---------- export ----------
  const handleExport = async () => {
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
  };

  // ---------- archive ----------
  const handleArchive = useCallback(
    async (paper: Paper) => {
      try {
        await archivePaper(paper);
        setArchivedTitles((prev) => new Set(prev).add(paper.title));
      } catch (e) {
        console.error("Archive failed:", e);
      }
    },
    [setArchivedTitles],
  );

  return (
    <div className="flex">
      <SearchPanel
        sources={sources}
        searchMode={searchMode}
        highImpactOnly={highImpactOnly}
        loading={loading}
        keywords={keywords}
        mode={mode}
        onSourceToggle={(key) =>
          setSources((prev) => ({ ...prev, [key]: !prev[key] }))
        }
        onSearchModeChange={setSearchMode}
        onHighImpactChange={setHighImpactOnly}
        onModeChange={setMode}
        onFetch={() => handleFetch()}
      />

      <PaperFeed
        result={result}
        papers={filteredPapers}
        loading={loading}
        error={error}
        sources={sources}
        searchQuery={searchQuery}
        onSearchQueryChange={setSearchQuery}
        onExport={handleExport}
        archivedTitles={archivedTitles}
        onArchive={handleArchive}
      />

      <DashboardPanel
        papers={filteredPapers}
        allPapers={result?.papers || []}
        loading={loading}
      />
    </div>
  );
}
