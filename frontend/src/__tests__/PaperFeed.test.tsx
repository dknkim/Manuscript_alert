import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import PaperFeed from "@/components/features/PaperFeed";
import { mockFetchResult } from "./fixtures";

const defaultProps = {
  result: null,
  papers: [],
  loading: false,
  error: null,
  sources: {
    pubmed: true,
    arxiv: false,
    biorxiv: false,
    medrxiv: false,
  },
  searchQuery: "",
  onSearchQueryChange: vi.fn(),
  onExport: vi.fn(),
  archivedTitles: new Set<string>(),
  onArchive: vi.fn(),
  displayState: { sources: [], phases: [] },
  isStreaming: false,
};

describe("PaperFeed", () => {
  it("shows a persistent fetching status while loading", () => {
    render(<PaperFeed {...defaultProps} loading={true} isStreaming={true} />);

    expect(screen.getByRole("status")).toHaveTextContent("Fetching papers...");
  });

  it("keeps fetching status visible while refreshing existing results", () => {
    render(
      <PaperFeed
        {...defaultProps}
        result={mockFetchResult}
        papers={mockFetchResult.papers}
        loading={true}
        isStreaming={true}
      />,
    );

    expect(screen.getByRole("status")).toHaveTextContent("Fetching papers...");
  });

  it("keeps status visible while scores are being calculated after sources finish", () => {
    render(
      <PaperFeed
        {...defaultProps}
        loading={false}
        isStreaming={false}
        displayState={{
          sources: [
            {
              source: "PubMed",
              status: "complete",
              papersFound: 12,
              steps: [],
            },
          ],
          phases: [
            {
              phase: "scoring",
              status: "active",
              totalPapers: 12,
            },
          ],
        }}
      />,
    );

    expect(screen.getByRole("status")).toHaveTextContent("Calculating scores...");
  });

  it("hides status after final results are available", () => {
    render(
      <PaperFeed
        {...defaultProps}
        result={mockFetchResult}
        papers={mockFetchResult.papers}
        displayState={{
          sources: [
            {
              source: "PubMed",
              status: "complete",
              papersFound: 12,
              steps: [],
            },
          ],
          phases: [
            {
              phase: "scoring",
              status: "done",
              totalPapers: 12,
            },
          ],
        }}
      />,
    );

    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });
});
