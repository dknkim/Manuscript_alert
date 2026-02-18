import React, { useState } from "react";

const SOURCE_COLORS = {
  PubMed: "bg-orange-500",
  arXiv: "bg-red-700",
  BioRxiv: "bg-emerald-600",
  Biorxiv: "bg-emerald-600",
  MedRxiv: "bg-blue-600",
  Medrxiv: "bg-blue-600",
};

function scoreColor(score) {
  if (score >= 7.5) return "text-green-600 border-green-500";
  if (score >= 5) return "text-amber-500 border-amber-400";
  if (score >= 2.5) return "text-orange-600 border-orange-400";
  return "text-red-600 border-red-500";
}

export default function PaperCard({ paper }) {
  const [expanded, setExpanded] = useState(false);
  const badge = SOURCE_COLORS[paper.source] || "bg-gray-500";
  const colors = scoreColor(paper.relevance_score);

  const abstract =
    !expanded && paper.abstract.length > 300
      ? paper.abstract.slice(0, 300) + "..."
      : paper.abstract;

  return (
    <div
      className={`bg-white rounded-xl border ${
        paper.is_high_impact
          ? "border-amber-400 shadow-md shadow-amber-100"
          : "border-gray-200"
      } p-5 transition-all hover:shadow-md`}
    >
      <div className="flex gap-5">
        {/* Main content */}
        <div className="flex-1 min-w-0">
          {/* Title */}
          {paper.url ? (
            <a
              href={paper.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-lg font-semibold text-gray-900 hover:text-indigo-600 transition-colors leading-snug"
            >
              {paper.title}
            </a>
          ) : (
            <h3 className="text-lg font-semibold text-gray-900 leading-snug">
              {paper.title}
            </h3>
          )}

          {/* Meta */}
          <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-gray-500">
            <span>{paper.authors}</span>
            <span className="text-gray-300">|</span>
            <span>{paper.published}</span>
          </div>

          {/* Journal */}
          {paper.journal && (
            <div className="mt-1.5 text-sm">
              <span className="text-gray-600 font-medium">
                {paper.journal}
              </span>
              {paper.volume && (
                <span className="text-gray-400">
                  , Vol.&nbsp;{paper.volume}
                </span>
              )}
              {paper.issue && (
                <span className="text-gray-400">
                  , Issue&nbsp;{paper.issue}
                </span>
              )}
              {paper.is_high_impact && (
                <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                  ⭐ Relevant Journal
                </span>
              )}
            </div>
          )}

          {/* Abstract */}
          <p className="mt-3 text-sm text-gray-600 leading-relaxed">
            {abstract}
            {paper.abstract.length > 300 && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="ml-1 text-indigo-600 hover:text-indigo-800 font-medium"
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
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700"
                >
                  {kw}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Score + badge column */}
        <div className="flex flex-col items-center gap-3 flex-shrink-0 w-24">
          <span
            className={`inline-block px-3 py-1 rounded-full text-xs font-bold text-white ${badge}`}
          >
            {paper.source}
          </span>
          <div
            className={`flex flex-col items-center justify-center border-2 rounded-xl px-3 py-2 ${colors}`}
          >
            <span className="text-2xl font-bold leading-none">
              {paper.relevance_score.toFixed(1)}
            </span>
            <span className="text-[10px] text-gray-400 mt-0.5">Score</span>
          </div>
        </div>
      </div>
    </div>
  );
}
