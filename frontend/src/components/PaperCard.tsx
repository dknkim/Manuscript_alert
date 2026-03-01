"use client";

import { useState } from "react";
import { Bookmark, BookmarkCheck } from "lucide-react";
import type { Paper } from "@/types";
import SourceBadge from "@/components/ui/SourceBadge";
import ScoreIndicator, {
  scoreAccentBorder,
} from "@/components/ui/ScoreIndicator";

interface PaperCardProps {
  paper: Paper;
  isArchived: boolean;
  onArchive: (paper: Paper) => void;
}

export default function PaperCard({
  paper,
  isArchived,
  onArchive,
}: PaperCardProps) {
  const [expanded, setExpanded] = useState<boolean>(false);

  const abstract =
    !expanded && paper.abstract.length > 300
      ? paper.abstract.slice(0, 300) + "..."
      : paper.abstract;

  return (
    <div
      className={`relative bg-surface-raised rounded-xl border-l-4 border ${
        paper.is_high_impact
          ? "border-amber-400 dark:border-amber-600 shadow-md shadow-amber-100/50 dark:shadow-amber-900/20"
          : "border-border"
      } ${scoreAccentBorder(paper.relevance_score)} p-5 transition-all hover:shadow-md`}
    >
      {/* Card-level "Relevant" tag — PubMed target journal match only
          (arXiv/bioRxiv/medRxiv are preprints, is_high_impact is always false) */}
      {paper.is_high_impact && (
        <span className="absolute -top-3 right-6 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-amber-400 dark:bg-amber-600 text-white shadow-sm">
          Relevant
        </span>
      )}

      <div className="flex gap-5">
        {/* Main content */}
        <div className="flex-1 min-w-0">
          {paper.url ? (
            <a
              href={paper.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-lg font-semibold text-text-primary hover:text-accent transition-colors leading-snug"
              onClick={(e) => e.stopPropagation()}
            >
              {paper.title}
            </a>
          ) : (
            <h3 className="text-lg font-semibold text-text-primary leading-snug">
              {paper.title}
            </h3>
          )}

          {/* Meta */}
          <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-text-muted">
            <span>{paper.authors}</span>
            <span className="text-border">|</span>
            <span>{paper.published}</span>
          </div>

          {/* Journal */}
          {paper.journal && (
            <div className="mt-1.5 text-sm">
              <span className="text-text-secondary font-medium">
                {paper.journal}
              </span>
              {paper.volume && (
                <span className="text-text-muted">
                  , Vol.&nbsp;{paper.volume}
                </span>
              )}
              {paper.issue && (
                <span className="text-text-muted">
                  , Issue&nbsp;{paper.issue}
                </span>
              )}
            </div>
          )}

          {/* Abstract */}
          <p className="mt-3 text-sm text-text-secondary leading-relaxed">
            {abstract}
            {paper.abstract.length > 300 && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setExpanded(!expanded);
                }}
                className="ml-1 text-accent hover:text-accent-hover font-medium"
              >
                {expanded ? "Show less" : "Show more"}
              </button>
            )}
          </p>

          {/* Keywords */}
          {paper.matched_keywords?.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {paper.matched_keywords.map((kw) => (
                <span
                  key={kw}
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-accent-subtle text-accent-text"
                >
                  {kw}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Score + badge + archive column */}
        <div className="flex flex-col items-center gap-3 shrink-0 w-24">
          <SourceBadge source={paper.source} />
          <ScoreIndicator score={paper.relevance_score} />
          <button
            onClick={(e) => {
              e.stopPropagation();
              onArchive(paper);
            }}
            disabled={isArchived}
            className={`w-full px-2 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center justify-center gap-1.5 ${
              isArchived
                ? "bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300 cursor-default"
                : "bg-surface-inset text-text-secondary hover:bg-accent-subtle hover:text-accent-text"
            }`}
            title={isArchived ? "Already archived" : "Archive this paper"}
          >
            {isArchived ? (
              <><BookmarkCheck className="size-3.5" /> Archived</>
            ) : (
              <><Bookmark className="size-3.5" /> Archive</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
