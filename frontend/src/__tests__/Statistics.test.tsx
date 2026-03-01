import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect } from "vitest";
import Statistics from "@/components/Statistics";
import { mockPaperHighImpact, mockPaperLowScore, mockPaperMedScore } from "./fixtures";

const papers = [mockPaperHighImpact, mockPaperMedScore, mockPaperLowScore];

describe("Statistics", () => {
  it("returns null when allPapers is empty", () => {
    const { container } = render(<Statistics papers={[]} allPapers={[]} />);
    expect(container.innerHTML).toBe("");
  });

  it("shows total papers count", () => {
    render(<Statistics papers={papers} allPapers={papers} />);
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("Total Papers")).toBeInTheDocument();
  });

  it("shows average score", () => {
    // avg = (8.5 + 5.5 + 2.0) / 3 = 5.3
    render(<Statistics papers={papers} allPapers={papers} />);
    expect(screen.getByText("5.3")).toBeInTheDocument();
  });

  it("shows max score", () => {
    render(<Statistics papers={papers} allPapers={papers} />);
    // max = Math.max(8.5, 5.5, 2.0) = 8.5
    expect(screen.getByText("8.5")).toBeInTheDocument();
  });

  it("shows source breakdown", () => {
    render(<Statistics papers={papers} allPapers={papers} />);
    expect(screen.getByText("PubMed")).toBeInTheDocument();
    expect(screen.getByText("arXiv")).toBeInTheDocument();
    expect(screen.getByText("BioRxiv")).toBeInTheDocument();
  });

  it("shows journal quality section when high-impact papers exist", () => {
    render(<Statistics papers={papers} allPapers={papers} />);
    expect(screen.getByText(/Journal Quality/)).toBeInTheDocument();
    expect(screen.getByText("Relevant Journals")).toBeInTheDocument();
  });

  it("hides journal quality section when no high-impact papers", () => {
    const lowPapers = [mockPaperLowScore, mockPaperMedScore];
    render(<Statistics papers={lowPapers} allPapers={lowPapers} />);
    expect(screen.queryByText(/Journal Quality/)).not.toBeInTheDocument();
  });

  it("shows top keywords section (collapsed by default)", async () => {
    const user = userEvent.setup();
    render(<Statistics papers={papers} allPapers={papers} />);

    // Top Keywords section exists but is collapsed
    const btn = screen.getByText(/Top Keywords/);
    expect(btn).toBeInTheDocument();

    // Expand it
    await user.click(btn);
    // Should show keyword names from our mock papers
    expect(screen.getByText("dementia")).toBeInTheDocument();
  });

  it("overview section is open by default", () => {
    render(<Statistics papers={papers} allPapers={papers} />);
    // Avg Score metric visible without clicking
    expect(screen.getByText("Avg Score")).toBeInTheDocument();
  });
});
