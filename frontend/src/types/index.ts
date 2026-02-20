/* ──────────────────────────────────────────────────────────────
   Shared TypeScript types for the Manuscript Alert frontend
   ────────────────────────────────────────────────────────────── */

export interface Paper {
  title: string;
  authors: string;
  abstract: string;
  published: string;
  url: string;
  source: string;
  relevance_score: number;
  matched_keywords: string[];
  journal: string;
  volume: string;
  issue: string;
  is_high_impact: boolean;
}

export interface FetchResult {
  papers: Paper[];
  total_before_filter: number;
  total_after_filter: number;
  errors: string[];
  must_have_keywords: string[];
}

export interface DataSources {
  arxiv: boolean;
  biorxiv: boolean;
  medrxiv: boolean;
  pubmed: boolean;
}

export interface KeywordScoring {
  high_priority: { keywords: string[]; boost: number };
  medium_priority: { keywords: string[]; boost: number };
}

export interface SearchSettings {
  days_back: number;
  search_mode: string;
  min_keyword_matches: number;
  max_results_display: number;
  default_sources: DataSources;
  journal_quality_filter: boolean;
}

export interface Settings {
  keywords: string[];
  journal_scoring: {
    enabled: boolean;
    high_impact_journal_boost: Record<string, number>;
  };
  target_journals: {
    exact_matches: string[];
    family_matches: string[];
    specific_journals: string[];
  };
  journal_exclusions: string[];
  keyword_scoring: KeywordScoring;
  search_settings: SearchSettings;
  ui_settings: Record<string, unknown>;
  must_have_keywords: string[];
}

export interface ModelInfo {
  name: string;
  filename: string;
  modified: string;
}

export interface BackupInfo {
  path: string;
  name: string;
  date: string;
}

export interface FlashMessage {
  text: string;
  type: "success" | "error";
}
