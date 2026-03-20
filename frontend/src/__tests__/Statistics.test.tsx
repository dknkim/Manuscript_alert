import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import Statistics from "@/components/Statistics";
import { mockPaperHighImpact, mockPaperLowScore, mockPaperMedScore } from "./fixtures";

const allPapers = [mockPaperHighImpact, mockPaperMedScore, mockPaperLowScore];

// When the filter is active, the parent passes only high-impact papers as `papers`
const filteredPapers = [mockPaperHighImpact];

describe("Statistics", () => {
  it("returns null when allPapers is empty", () => {
    const { container } = render(<Statistics papers={[]} allPapers={[]} />);
    expect(container.innerHTML).toBe("");
  });

  it("shows total papers count", () => {
    render(<Statistics papers={allPapers} allPapers={allPapers} />);
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("Total Papers")).toBeInTheDocument();
  });

  it("shows average score", () => {
    // avg = (8.5 + 5.5 + 2.0) / 3 = 5.3
    render(<Statistics papers={allPapers} allPapers={allPapers} />);
    expect(screen.getByText("5.3")).toBeInTheDocument();
  });

  it("shows max score", () => {
    // max = Math.max(8.5, 5.5, 2.0) = 8.5
    render(<Statistics papers={allPapers} allPapers={allPapers} />);
    expect(screen.getByText("8.5")).toBeInTheDocument();
  });

  it("shows source breakdown from allPapers when filter is off", () => {
    render(<Statistics papers={allPapers} allPapers={allPapers} highImpactOnly={false} />);
    expect(screen.getByText("PubMed")).toBeInTheDocument();
    expect(screen.getByText("arXiv")).toBeInTheDocument();
    expect(screen.getByText("BioRxiv")).toBeInTheDocument();
  });

  it("shows source breakdown from filtered papers when filter is on", () => {
    render(
      <Statistics
        papers={filteredPapers}
        allPapers={allPapers}
        highImpactOnly={true}
        onHighImpactChange={vi.fn()}
      />,
    );
    // Only PubMed (the high-impact paper's source) should appear
    expect(screen.getByText("PubMed")).toBeInTheDocument();
    expect(screen.queryByText("arXiv")).not.toBeInTheDocument();
    expect(screen.queryByText("BioRxiv")).not.toBeInTheDocument();
  });

  it("shows filtered indicator in Sources when filter is active", () => {
    render(
      <Statistics
        papers={filteredPapers}
        allPapers={allPapers}
        highImpactOnly={true}
        onHighImpactChange={vi.fn()}
      />,
    );
    expect(screen.getByText("filtered")).toBeInTheDocument();
  });

  it("does not show filtered indicator when filter is off", () => {
    render(
      <Statistics
        papers={allPapers}
        allPapers={allPapers}
        highImpactOnly={false}
        onHighImpactChange={vi.fn()}
      />,
    );
    expect(screen.queryByText("filtered")).not.toBeInTheDocument();
  });

  it("shows relevant journals toggle when high-impact papers exist", () => {
    render(<Statistics papers={allPapers} allPapers={allPapers} />);
    expect(screen.getByText("Relevant Journals")).toBeInTheDocument();
  });

  it("hides the filters section when no high-impact papers exist", () => {
    const lowPapers = [mockPaperLowScore, mockPaperMedScore];
    render(<Statistics papers={lowPapers} allPapers={lowPapers} />);
    expect(screen.queryByText("Relevant Journals")).not.toBeInTheDocument();
    expect(screen.queryByText("Filters")).not.toBeInTheDocument();
  });

  it("shows keywords visible by default (flat layout)", () => {
    render(<Statistics papers={allPapers} allPapers={allPapers} />);
    // Keywords are visible without clicking — no accordion
    expect(screen.getByText("dementia")).toBeInTheDocument();
  });

  it("all stats visible without clicking (flat layout)", () => {
    render(<Statistics papers={allPapers} allPapers={allPapers} />);
    expect(screen.getByText("Avg Score")).toBeInTheDocument();
    expect(screen.getByText("Score Summary")).toBeInTheDocument();
    expect(screen.getByText("Sources")).toBeInTheDocument();
    expect(screen.getByText("Top Keywords")).toBeInTheDocument();
  });

  it("calls onHighImpactChange when Relevant Journals is clicked", async () => {
    const handler = vi.fn();
    render(
      <Statistics
        papers={allPapers}
        allPapers={allPapers}
        highImpactOnly={false}
        onHighImpactChange={handler}
      />,
    );
    await userEvent.click(screen.getByText("Relevant Journals"));
    expect(handler).toHaveBeenCalledWith(true);
  });

  it("toggles off when clicked while active", async () => {
    const handler = vi.fn();
    render(
      <Statistics
        papers={filteredPapers}
        allPapers={allPapers}
        highImpactOnly={true}
        onHighImpactChange={handler}
      />,
    );
    await userEvent.click(screen.getByText("Relevant Journals"));
    expect(handler).toHaveBeenCalledWith(false);
  });

  it("shows active styling when highImpactOnly is true", () => {
    render(
      <Statistics
        papers={filteredPapers}
        allPapers={allPapers}
        highImpactOnly={true}
        onHighImpactChange={vi.fn()}
      />,
    );
    const button = screen.getByText("Relevant Journals").closest("button");
    expect(button?.className).toContain("ring-1");
    expect(button?.className).toContain("bg-amber-100");
  });

  it("shows inactive styling when highImpactOnly is false", () => {
    render(
      <Statistics
        papers={allPapers}
        allPapers={allPapers}
        highImpactOnly={false}
        onHighImpactChange={vi.fn()}
      />,
    );
    const button = screen.getByText("Relevant Journals").closest("button");
    // Inactive state uses bg-amber-50 (not the solid bg-amber-100 active fill).
    // Note: hover:bg-amber-100/80 appears in the class string as a hover utility,
    // so we check that the standalone active class is absent via a word-boundary regex.
    expect(button?.className).toContain("bg-amber-50");
    expect(button?.className).not.toMatch(/(?<![:/\w])bg-amber-100(?![\w/])/);
  });

  it("toggle has aria-pressed reflecting active state", () => {
    render(
      <Statistics
        papers={filteredPapers}
        allPapers={allPapers}
        highImpactOnly={true}
        onHighImpactChange={vi.fn()}
      />,
    );
    const button = screen.getByText("Relevant Journals").closest("button");
    expect(button).toHaveAttribute("aria-pressed", "true");
  });

  it("toggle has aria-pressed false when inactive", () => {
    render(
      <Statistics
        papers={allPapers}
        allPapers={allPapers}
        highImpactOnly={false}
        onHighImpactChange={vi.fn()}
      />,
    );
    const button = screen.getByText("Relevant Journals").closest("button");
    expect(button).toHaveAttribute("aria-pressed", "false");
  });
});
