import React, { useState, useEffect, useRef, useMemo, useCallback } from "react";
import { fetchPapers, exportPapersCSV } from "../api";
import PaperCard from "./PaperCard";
import Statistics from "./Statistics";

const SEARCH_MODES = [
  {
    value: "Brief (PubMed: 1000, Others: 500)",
    label: "Brief",
    hint: "Fastest results with recent papers.",
  },
  {
    value: "Standard (PubMed: 2500, Others: 1000)",
    label: "Standard",
    hint: "Balanced for speed and coverage.",
  },
  {
    value: "Extended (All sources: 5000)",
    label: "Extended",
    hint: "May take 2-3x longer but comprehensive.",
  },
];

export default function PapersTab({
  settings,
  result,
  setResult,
  loading,
  setLoading,
  error,
  setError,
}) {
  const searchSettings = settings.search_settings || {};

  const [sources, setSources] = useState({
    arxiv: true,
    biorxiv: true,
    medrxiv: true,
    pubmed: true,
  });
  const [searchMode, setSearchMode] = useState(SEARCH_MODES[0].value);
  const [highImpactOnly, setHighImpactOnly] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const keywords = settings.keywords || [];

  // ---------- fetch ----------
  const handleFetch = useCallback(async (overrideSources) => {
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
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [sources, searchMode, keywords, setResult, setLoading, setError]);

  // ---------- auto-fetch on first load ----------
  const didAutoFetch = useRef(false);
  useEffect(() => {
    if (!didAutoFetch.current && keywords.length > 0 && !result) {
      didAutoFetch.current = true;
      const allSources = { arxiv: true, biorxiv: true, medrxiv: true, pubmed: true };
      handleFetch(allSources);
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
          p.authors.toLowerCase().includes(q)
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

  const toggleSource = (key) =>
    setSources((prev) => ({ ...prev, [key]: !prev[key] }));

  return (
    <div className="flex">
      {/* ---------- Sidebar ---------- */}
      <aside className="w-72 flex-shrink-0 bg-white border-r border-gray-200 p-5 space-y-6 sticky top-[73px] h-[calc(100vh-73px)] overflow-y-auto">
        <div>
          <h2 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-3">
            🔧 Configuration
          </h2>
        </div>

        {/* Journal Quality */}
        <div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">
            Journal Quality
          </h3>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={highImpactOnly}
              onChange={() => setHighImpactOnly(!highImpactOnly)}
              className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
            <span className="text-sm text-gray-700">
              🌟 Relevant Journals Only
            </span>
          </label>
        </div>

        {/* Search Mode */}
        <div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">
            Search Limits
          </h3>
          <div className="space-y-2">
            {SEARCH_MODES.map((mode) => (
              <label
                key={mode.value}
                className="flex items-start gap-2 cursor-pointer"
              >
                <input
                  type="radio"
                  name="searchMode"
                  value={mode.value}
                  checked={searchMode === mode.value}
                  onChange={() => setSearchMode(mode.value)}
                  className="mt-0.5 text-indigo-600 focus:ring-indigo-500"
                />
                <div>
                  <span className="text-sm font-medium text-gray-700">
                    {mode.label}
                  </span>
                  <p className="text-xs text-gray-400">{mode.hint}</p>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Data Sources */}
        <div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">
            Data Sources
          </h3>
          <div className="grid grid-cols-2 gap-2">
            {[
              { key: "arxiv", label: "arXiv" },
              { key: "biorxiv", label: "bioRxiv" },
              { key: "medrxiv", label: "medRxiv" },
              { key: "pubmed", label: "PubMed" },
            ].map((s) => (
              <label key={s.key} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={sources[s.key]}
                  onChange={() => toggleSource(s.key)}
                  className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-sm text-gray-700">{s.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Fetch button */}
        <button
          onClick={() => handleFetch()}
          disabled={loading}
          className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white rounded-lg text-sm font-semibold transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
              Fetching…
            </>
          ) : (
            "🔍 Fetch Papers"
          )}
        </button>

        {/* Keywords preview */}
        <div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">
            Active Keywords ({keywords.length})
          </h3>
          <div className="flex flex-wrap gap-1">
            {keywords.slice(0, 12).map((kw) => (
              <span
                key={kw}
                className="text-xs px-2 py-0.5 bg-gray-100 rounded-full text-gray-600"
              >
                {kw}
              </span>
            ))}
            {keywords.length > 12 && (
              <span className="text-xs text-gray-400">
                +{keywords.length - 12} more
              </span>
            )}
          </div>
        </div>
      </aside>

      {/* ---------- Main Content ---------- */}
      <div className="flex-1 flex">
        <div className="flex-1 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-900">Recent Papers</h2>
            {result && (
              <button
                onClick={handleExport}
                className="text-sm text-indigo-600 hover:text-indigo-800 font-medium"
              >
                📥 Export CSV
              </button>
            )}
          </div>

          {/* Search within results */}
          {result && (
            <input
              type="text"
              placeholder="🔍 Search within results…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
            />
          )}

          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* API errors */}
          {result?.errors?.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 text-amber-700 px-4 py-3 rounded-lg text-sm">
              {result.errors.map((e, i) => (
                <div key={i}>⚠️ {e}</div>
              ))}
            </div>
          )}

          {/* Must-have info */}
          {result?.must_have_keywords?.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 text-blue-700 px-4 py-3 rounded-lg text-sm">
              🔒 Must-have filter active: papers must match one of{" "}
              <strong>{result.must_have_keywords.join(", ")}</strong>
            </div>
          )}

          {/* Result count */}
          {result && (
            <p className="text-sm text-gray-500">
              <strong>{filteredPapers.length}</strong> papers displayed
              {result.total_before_filter !== result.total_after_filter && (
                <span>
                  {" "}
                  ({result.total_before_filter - result.total_after_filter}{" "}
                  excluded by filters)
                </span>
              )}
            </p>
          )}

          {/* Loading */}
          {loading && (
            <div className="flex flex-col items-center justify-center py-20 text-gray-400">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600 mb-4" />
              <p className="text-sm">
                Fetching papers from{" "}
                {Object.entries(sources)
                  .filter(([, v]) => v)
                  .map(([k]) => k.toUpperCase())
                  .join(", ")}
                …
              </p>
            </div>
          )}

          {/* Empty state */}
          {!loading && !result && (
            <div className="text-center py-20 text-gray-400">
              <p className="text-4xl mb-3">📄</p>
              <p className="text-lg font-medium">No papers loaded yet</p>
              <p className="text-sm mt-1">
                Configure sources in the sidebar and click{" "}
                <strong>Fetch Papers</strong>.
              </p>
            </div>
          )}

          {/* Papers list */}
          {!loading && filteredPapers.length > 0 && (
            <div className="space-y-4">
              {filteredPapers.map((paper, idx) => (
                <PaperCard key={`${paper.title}-${idx}`} paper={paper} />
              ))}
            </div>
          )}

          {/* No results after fetch */}
          {!loading && result && filteredPapers.length === 0 && (
            <div className="text-center py-16 text-gray-400">
              <p className="text-4xl mb-3">🔍</p>
              <p className="text-lg font-medium">No papers found</p>
              <p className="text-sm mt-1">
                Try adjusting your keywords or date range in Settings.
              </p>
            </div>
          )}
        </div>

        {/* ---------- Stats sidebar ---------- */}
        {result && filteredPapers.length > 0 && (
          <aside className="w-72 flex-shrink-0 border-l border-gray-200 bg-white p-5 sticky top-[73px] h-[calc(100vh-73px)] overflow-y-auto">
            <h2 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4">
              📊 Statistics
            </h2>
            <Statistics papers={filteredPapers} allPapers={result.papers} />
          </aside>
        )}
      </div>
    </div>
  );
}
