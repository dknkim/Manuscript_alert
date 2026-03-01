"use client";

import { useSettings } from "@/hooks/useSettings";
import { usePaperSearch } from "@/hooks/usePaperSearch";
import SearchPanel from "@/components/features/SearchPanel";
import PaperFeed from "@/components/features/PaperFeed";
import DashboardPanel from "@/components/features/DashboardPanel";
import Spinner from "@/components/ui/Spinner";

export default function PapersPage() {
  const { settings } = useSettings();
  const keywords = settings?.keywords || [];
  const search = usePaperSearch(
    keywords,
    settings?.search_settings?.default_sources,
  );

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
        loading={search.loading}
        keywords={keywords}
        mode="classic"
        onSourceToggle={search.toggleSource}
        onSearchModeChange={search.setSearchMode}
        onHighImpactChange={search.setHighImpactOnly}
        onModeChange={() => {}}
        onFetch={() => search.fetch()}
      />

      <PaperFeed
        result={search.result}
        papers={search.filteredPapers}
        loading={search.loading}
        error={search.error}
        sources={search.sources}
        searchQuery={search.searchQuery}
        onSearchQueryChange={search.setSearchQuery}
        onExport={search.exportCSV}
        archivedTitles={search.archivedTitles}
        onArchive={search.archive}
      />

      <DashboardPanel
        papers={search.filteredPapers}
        allPapers={search.result?.papers || []}
        loading={search.loading}
      />
    </div>
  );
}
