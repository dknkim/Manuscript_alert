import type { Paper, Settings, FetchResult, ModelInfo, BackupInfo } from "@/types";

export const mockSettings: Settings = {
  keywords: ["Alzheimer's disease", "PET", "MRI", "dementia", "amyloid", "tau"],
  journal_scoring: {
    enabled: true,
    high_impact_journal_boost: {
      "5_or_more_keywords": 5.1,
      "4_keywords": 3.7,
      "3_keywords": 2.8,
      "2_keywords": 1.3,
      "1_keyword": 0.5,
    },
  },
  target_journals: {
    exact_matches: ["jama", "nature", "science"],
    family_matches: ["jama ", "nature "],
    specific_journals: ["alzheimer's & dementia"],
  },
  journal_exclusions: ["abdominal", "pediatric"],
  keyword_scoring: {
    high_priority: {
      keywords: ["Alzheimer's disease", "dementia"],
      boost: 1.5,
    },
    medium_priority: {
      keywords: ["PET", "MRI"],
      boost: 1.2,
    },
  },
  search_settings: {
    days_back: 7,
    search_mode: "Brief",
    min_keyword_matches: 2,
    max_results_display: 50,
    default_sources: {
      pubmed: true,
      arxiv: false,
      biorxiv: false,
      medrxiv: false,
    },
    journal_quality_filter: false,
  },
  ui_settings: { theme: "light" },
  must_have_keywords: [],
};

export const mockPaperHighImpact: Paper = {
  title: "Amyloid PET imaging in Alzheimer's disease diagnosis",
  authors: "Smith J, Doe A, Lee K",
  abstract:
    "Background: Amyloid PET imaging is a key diagnostic tool for Alzheimer's disease. " +
    "This systematic review evaluates recent advances in tau and amyloid PET tracers " +
    "for dementia diagnosis, covering over 50 clinical trials and 3000 participants. " +
    "Results demonstrate improved sensitivity and specificity of next-generation tracers.",
  published: "2026-02-20",
  url: "https://pubmed.ncbi.nlm.nih.gov/12345678",
  source: "PubMed",
  relevance_score: 8.5,
  matched_keywords: ["Alzheimer's disease", "PET", "amyloid", "tau", "dementia"],
  journal: "Nature Medicine",
  volume: "32",
  issue: "2",
  is_high_impact: true,
};

export const mockPaperLowScore: Paper = {
  title: "Brain MRI segmentation methods",
  authors: "Wang X, Chen Y",
  abstract: "A review of brain MRI segmentation approaches.",
  published: "2026-02-18",
  url: "https://arxiv.org/abs/2602.12345",
  source: "arXiv",
  relevance_score: 2.0,
  matched_keywords: ["MRI", "brain"],
  journal: "",
  volume: "",
  issue: "",
  is_high_impact: false,
};

export const mockPaperMedScore: Paper = {
  title: "Plasma biomarkers for early dementia detection",
  authors: "Johnson R, Kim S, Patel N",
  abstract: "Short abstract.",
  published: "2026-02-19",
  url: "",
  source: "BioRxiv",
  relevance_score: 5.5,
  matched_keywords: ["dementia", "plasma"],
  journal: "bioRxiv preprint",
  volume: "",
  issue: "",
  is_high_impact: false,
};

export const mockFetchResult: FetchResult = {
  papers: [mockPaperHighImpact, mockPaperMedScore, mockPaperLowScore],
  total_before_filter: 10,
  total_after_filter: 3,
  errors: [],
  must_have_keywords: [],
};

export const mockModels: ModelInfo[] = [
  { name: "AD Neuroimaging", filename: "AD_Neuroimaging.json", modified: "2026-02-20 14:30" },
  { name: "Tau PET Focus", filename: "Tau_PET_Focus.json", modified: "2026-02-19 10:15" },
];

export const mockBackups: BackupInfo[] = [
  { path: "/tmp/backups/settings_backup_20260227.py", name: "settings_backup_20260227.py", date: "20260227_143000" },
  { path: "/tmp/backups/settings_backup_20260226.py", name: "settings_backup_20260226.py", date: "20260226_101500" },
];
