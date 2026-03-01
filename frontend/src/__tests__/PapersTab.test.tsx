import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import PapersTab from "@/components/PapersTab";
import { mockSettings, mockFetchResult } from "./fixtures";

// Mock the API module
vi.mock("@/lib/api", () => ({
  fetchPapers: vi.fn(),
  exportPapersCSV: vi.fn(),
  archivePaper: vi.fn(),
}));

import { fetchPapers, archivePaper } from "@/lib/api";

const defaultProps = () => ({
  settings: mockSettings,
  result: null as ReturnType<typeof mockFetchResult> | null,
  setResult: vi.fn(),
  loading: false,
  setLoading: vi.fn(),
  error: null as string | null,
  setError: vi.fn(),
  archivedTitles: new Set<string>(),
  setArchivedTitles: vi.fn(),
});

describe("PapersTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows empty state when no result", () => {
    render(<PapersTab {...defaultProps()} />);
    expect(screen.getByText(/No papers loaded yet/)).toBeInTheDocument();
  });

  it("shows loading skeleton when loading", () => {
    render(<PapersTab {...defaultProps()} loading={true} />);
    // Skeleton cards have animate-pulse class during loading
    const skeletons = document.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("shows error message when error is set", () => {
    render(<PapersTab {...defaultProps()} error="Network error" />);
    expect(screen.getByText("Network error")).toBeInTheDocument();
  });

  it("displays all 4 data source checkboxes", () => {
    render(<PapersTab {...defaultProps()} />);
    expect(screen.getByLabelText("arXiv")).toBeInTheDocument();
    expect(screen.getByLabelText("bioRxiv")).toBeInTheDocument();
    expect(screen.getByLabelText("medRxiv")).toBeInTheDocument();
    expect(screen.getByLabelText("PubMed")).toBeInTheDocument();
  });

  it("displays 3 search mode radio buttons", () => {
    render(<PapersTab {...defaultProps()} />);
    expect(screen.getByLabelText(/Brief/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Standard/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Extended/)).toBeInTheDocument();
  });

  it("displays keywords count", () => {
    render(<PapersTab {...defaultProps()} />);
    expect(screen.getByText(`Active Keywords (${mockSettings.keywords.length})`)).toBeInTheDocument();
  });

  it("shows fetch button", () => {
    render(<PapersTab {...defaultProps()} />);
    expect(screen.getByRole("button", { name: /Fetch Papers/ })).toBeInTheDocument();
  });

  it("disables fetch button when loading", () => {
    render(<PapersTab {...defaultProps()} loading={true} />);
    const btn = screen.getByRole("button", { name: /Fetching/ });
    expect(btn).toBeDisabled();
  });

  it("renders papers when result is provided", () => {
    render(<PapersTab {...defaultProps()} result={mockFetchResult} />);
    expect(screen.getByText(mockFetchResult.papers[0].title)).toBeInTheDocument();
    expect(screen.getByText(mockFetchResult.papers[1].title)).toBeInTheDocument();
  });

  it("shows result count", () => {
    render(<PapersTab {...defaultProps()} result={mockFetchResult} />);
    expect(screen.getByText(/papers displayed/)).toBeInTheDocument();
  });

  it("shows export CSV button when result exists", () => {
    render(<PapersTab {...defaultProps()} result={mockFetchResult} />);
    expect(screen.getByText(/Export CSV/)).toBeInTheDocument();
  });

  it("hides export CSV button when no result", () => {
    render(<PapersTab {...defaultProps()} />);
    expect(screen.queryByText(/Export CSV/)).not.toBeInTheDocument();
  });

  it("shows search input when result exists", () => {
    render(<PapersTab {...defaultProps()} result={mockFetchResult} />);
    expect(screen.getByPlaceholderText(/Search within results/)).toBeInTheDocument();
  });

  it("shows 'no papers found' when result has empty papers", () => {
    const emptyResult = { ...mockFetchResult, papers: [] };
    render(<PapersTab {...defaultProps()} result={emptyResult} />);
    expect(screen.getByText(/No papers found/)).toBeInTheDocument();
  });

  it("shows journal quality toggle", () => {
    render(<PapersTab {...defaultProps()} />);
    expect(screen.getByLabelText(/Relevant Journals Only/)).toBeInTheDocument();
  });

  it("shows API errors when present", () => {
    const resultWithErrors = {
      ...mockFetchResult,
      errors: ["pubmed: timeout after 30s"],
    };
    render(<PapersTab {...defaultProps()} result={resultWithErrors} />);
    expect(screen.getByText(/pubmed: timeout after 30s/)).toBeInTheDocument();
  });

  it("shows must-have keywords info when present", () => {
    const resultWithMustHave = {
      ...mockFetchResult,
      must_have_keywords: ["Alzheimer's disease"],
    };
    render(<PapersTab {...defaultProps()} result={resultWithMustHave} />);
    expect(screen.getByText(/Must-have filter active/)).toBeInTheDocument();
  });

  it("shows statistics sidebar when papers exist", () => {
    render(<PapersTab {...defaultProps()} result={mockFetchResult} />);
    expect(screen.getByText(/Statistics/)).toBeInTheDocument();
  });

  it("shows filter exclusion count when filters reduce results", () => {
    render(<PapersTab {...defaultProps()} result={mockFetchResult} />);
    // total_before_filter(10) - total_after_filter(3) = 7 excluded
    expect(screen.getByText(/7 excluded by filters/)).toBeInTheDocument();
  });
});
