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

  it("shows relevant journals metric when high-impact papers exist", () => {
    render(<Statistics papers={papers} allPapers={papers} />);
    expect(screen.getByText("Relevant Journals")).toBeInTheDocument();
  });

  it("hides relevant journals metric when no high-impact papers", () => {
    const lowPapers = [mockPaperLowScore, mockPaperMedScore];
    render(<Statistics papers={lowPapers} allPapers={lowPapers} />);
    expect(screen.queryByText("Relevant Journals")).not.toBeInTheDocument();
  });

  it("shows keywords visible by default (flat layout)", () => {
    render(<Statistics papers={papers} allPapers={papers} />);
    // Keywords are visible without clicking — no accordion
    expect(screen.getByText("dementia")).toBeInTheDocument();
  });

  it("all stats visible without clicking (flat layout)", () => {
    render(<Statistics papers={papers} allPapers={papers} />);
    expect(screen.getByText("Avg Score")).toBeInTheDocument();
    expect(screen.getByText("Score Summary")).toBeInTheDocument();
    expect(screen.getByText("Sources")).toBeInTheDocument();
    expect(screen.getByText("Top Keywords")).toBeInTheDocument();
  });
});
