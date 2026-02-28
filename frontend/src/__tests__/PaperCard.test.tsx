import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import PaperCard from "@/components/PaperCard";
import { mockPaperHighImpact, mockPaperLowScore, mockPaperMedScore } from "./fixtures";

describe("PaperCard", () => {
  it("renders paper title, authors, and published date", () => {
    render(
      <PaperCard paper={mockPaperHighImpact} isArchived={false} onArchive={vi.fn()} />,
    );
    expect(screen.getByText(mockPaperHighImpact.title)).toBeInTheDocument();
    expect(screen.getByText(mockPaperHighImpact.authors)).toBeInTheDocument();
    expect(screen.getByText(mockPaperHighImpact.published)).toBeInTheDocument();
  });

  it("renders title as link when URL exists", () => {
    render(
      <PaperCard paper={mockPaperHighImpact} isArchived={false} onArchive={vi.fn()} />,
    );
    const link = screen.getByRole("link", { name: mockPaperHighImpact.title });
    expect(link).toHaveAttribute("href", mockPaperHighImpact.url);
    expect(link).toHaveAttribute("target", "_blank");
  });

  it("renders title as heading when no URL", () => {
    render(
      <PaperCard paper={mockPaperMedScore} isArchived={false} onArchive={vi.fn()} />,
    );
    const heading = screen.getByRole("heading", { name: mockPaperMedScore.title });
    expect(heading).toBeInTheDocument();
  });

  it("shows journal name, volume, and issue", () => {
    render(
      <PaperCard paper={mockPaperHighImpact} isArchived={false} onArchive={vi.fn()} />,
    );
    expect(screen.getByText("Nature Medicine")).toBeInTheDocument();
    expect(screen.getByText(/Vol\.\s*32/)).toBeInTheDocument();
    expect(screen.getByText(/Issue\s*2/)).toBeInTheDocument();
  });

  it("shows 'Relevant Journal' badge for high-impact papers", () => {
    render(
      <PaperCard paper={mockPaperHighImpact} isArchived={false} onArchive={vi.fn()} />,
    );
    expect(screen.getByText(/Relevant Journal/)).toBeInTheDocument();
  });

  it("does not show 'Relevant Journal' badge for non-high-impact papers", () => {
    render(
      <PaperCard paper={mockPaperLowScore} isArchived={false} onArchive={vi.fn()} />,
    );
    expect(screen.queryByText(/Relevant Journal/)).not.toBeInTheDocument();
  });

  it("displays relevance score", () => {
    render(
      <PaperCard paper={mockPaperHighImpact} isArchived={false} onArchive={vi.fn()} />,
    );
    expect(screen.getByText("8.5")).toBeInTheDocument();
  });

  it("displays source badge", () => {
    render(
      <PaperCard paper={mockPaperHighImpact} isArchived={false} onArchive={vi.fn()} />,
    );
    expect(screen.getByText("PubMed")).toBeInTheDocument();
  });

  it("displays matched keywords as pills", () => {
    render(
      <PaperCard paper={mockPaperHighImpact} isArchived={false} onArchive={vi.fn()} />,
    );
    for (const kw of mockPaperHighImpact.matched_keywords) {
      expect(screen.getByText(kw)).toBeInTheDocument();
    }
  });

  it("truncates long abstracts and shows 'Show more' button", () => {
    render(
      <PaperCard paper={mockPaperHighImpact} isArchived={false} onArchive={vi.fn()} />,
    );
    // Abstract is > 300 chars, should be truncated
    expect(screen.getByText(/Show more/)).toBeInTheDocument();
    expect(screen.queryByText(/Show less/)).not.toBeInTheDocument();
  });

  it("does not show 'Show more' for short abstracts", () => {
    render(
      <PaperCard paper={mockPaperMedScore} isArchived={false} onArchive={vi.fn()} />,
    );
    expect(screen.queryByText(/Show more/)).not.toBeInTheDocument();
  });

  it("expands and collapses abstract on toggle", async () => {
    const user = userEvent.setup();
    render(
      <PaperCard paper={mockPaperHighImpact} isArchived={false} onArchive={vi.fn()} />,
    );
    await user.click(screen.getByText(/Show more/));
    expect(screen.getByText(/Show less/)).toBeInTheDocument();

    await user.click(screen.getByText(/Show less/));
    expect(screen.getByText(/Show more/)).toBeInTheDocument();
  });

  it("shows archive button and calls onArchive when clicked", async () => {
    const user = userEvent.setup();
    const onArchive = vi.fn();
    render(
      <PaperCard paper={mockPaperHighImpact} isArchived={false} onArchive={onArchive} />,
    );

    const btn = screen.getByRole("button", { name: /Archive/ });
    expect(btn).not.toBeDisabled();
    await user.click(btn);
    expect(onArchive).toHaveBeenCalledWith(mockPaperHighImpact);
  });

  it("shows archived state when isArchived is true", () => {
    render(
      <PaperCard paper={mockPaperHighImpact} isArchived={true} onArchive={vi.fn()} />,
    );
    const btn = screen.getByRole("button", { name: /Archived/ });
    expect(btn).toBeDisabled();
  });

  // Score color regression tests
  it.each([
    { score: 8.5, expected: "green" },
    { score: 5.5, expected: "amber" },
    { score: 3.0, expected: "orange" },
    { score: 1.0, expected: "red" },
  ])("applies $expected color class for score $score", ({ score, expected }) => {
    const paper = { ...mockPaperLowScore, relevance_score: score };
    const { container } = render(
      <PaperCard paper={paper} isArchived={false} onArchive={vi.fn()} />,
    );
    const scoreEl = container.querySelector(`[class*="${expected}"]`);
    expect(scoreEl).toBeTruthy();
  });
});
