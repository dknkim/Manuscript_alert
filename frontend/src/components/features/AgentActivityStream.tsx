"use client";

import { useState, useEffect } from "react";
import {
  CheckCircle,
  AlertCircle,
  Loader,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import type {
  DisplayState,
  SourceNode,
  PhaseNode,
} from "@/hooks/useAgentStream";

interface AgentActivityStreamProps {
  displayState: DisplayState;
  isStreaming: boolean;
}

// ---------------------------------------------------------------------------
// Source row sub-components
// ---------------------------------------------------------------------------

function SourceIcon({ status }: { status: SourceNode["status"] }) {
  switch (status) {
    case "error":
      return <AlertCircle className="h-3.5 w-3.5 text-red-400 shrink-0" />;
    case "complete":
      return <CheckCircle className="h-3.5 w-3.5 text-accent shrink-0" />;
    default:
      return (
        <Loader className="h-3.5 w-3.5 text-accent animate-spin shrink-0" />
      );
  }
}

/** Right-aligned detail: batch progress, paper count, or error. */
function SourceDetail({ node }: { node: SourceNode }) {
  if (node.status === "error") {
    return (
      <span className="text-red-400/80 truncate text-right">
        {node.errorMessage}
      </span>
    );
  }
  if (node.status === "complete") {
    return (
      <span className="text-text-muted tabular-nums whitespace-nowrap">
        {node.papersFound?.toLocaleString()} papers
      </span>
    );
  }
  // Fetching — show batch progress if available
  if (node.batch != null && node.totalBatches != null) {
    return (
      <span className="text-text-muted tabular-nums whitespace-nowrap">
        batch {node.batch}/{node.totalBatches} &middot;{" "}
        {node.papersSoFar?.toLocaleString()} papers
      </span>
    );
  }
  return null;
}

// ---------------------------------------------------------------------------
// Phase row sub-components
// ---------------------------------------------------------------------------

function PhaseIcon({ status }: { status: PhaseNode["status"] }) {
  if (status === "done") {
    return <CheckCircle className="h-3.5 w-3.5 text-accent shrink-0" />;
  }
  return (
    <Loader className="h-3.5 w-3.5 text-accent animate-spin shrink-0" />
  );
}

function ScoringContent({ node }: { node: PhaseNode }) {
  const label =
    node.status === "active"
      ? `Scoring ${node.totalPapers?.toLocaleString() ?? ""} papers\u2026`
      : `Scored ${node.totalPapers?.toLocaleString() ?? ""} papers`;
  return (
    <>
      <span className="text-text-secondary">{label}</span>
      {node.criteria && node.criteria.length > 0 && (
        <span className="text-[10px] leading-tight text-text-muted mt-0.5">
          {node.criteria.join(" \u00b7 ")}
        </span>
      )}
    </>
  );
}

function FilteringContent({ node }: { node: PhaseNode }) {
  const parts: string[] = [];
  if (node.minKeywords) {
    parts.push(`\u2265${node.minKeywords} keyword matches required`);
  }
  if (node.mustHaveKeywords && node.mustHaveKeywords.length > 0) {
    parts.push(`must include: ${node.mustHaveKeywords.join(", ")}`);
  }
  return (
    <>
      <span className="text-text-secondary tabular-nums">
        {node.totalBefore?.toLocaleString()} &rarr;{" "}
        {node.totalAfter?.toLocaleString()} papers
      </span>
      {parts.length > 0 && (
        <span className="text-[10px] leading-tight text-text-muted mt-0.5">
          {parts.join(" \u00b7 ")}
        </span>
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function AgentActivityStream({
  displayState,
  isStreaming,
}: AgentActivityStreamProps) {
  const [expanded, setExpanded] = useState(true);
  const { sources, phases } = displayState;

  // Auto-expand on stream start; delayed collapse on finish
  useEffect(() => {
    if (isStreaming) {
      setExpanded(true);
      return;
    }
    if (sources.length > 0) {
      const timer = setTimeout(() => setExpanded(false), 800);
      return () => clearTimeout(timer);
    }
  }, [isStreaming, sources.length]);

  if (sources.length === 0 && !isStreaming) return null;

  // Summary stats for header
  const completeSources = sources.filter((s) => s.status === "complete");
  const errorCount = sources.filter((s) => s.status === "error").length;
  const totalPapers = completeSources.reduce(
    (sum, s) => sum + (s.papersFound ?? 0),
    0,
  );

  return (
    <div className="border border-border rounded-lg bg-surface-raised overflow-hidden">
      {/* Header — always visible, toggles expand */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-2.5 text-xs font-medium text-text-secondary hover:bg-surface-inset/50 transition-colors"
      >
        <span className="flex items-center gap-2">
          {isStreaming ? (
            <>
              <Loader className="h-3.5 w-3.5 animate-spin text-accent" />
              Fetching papers&hellip;
            </>
          ) : (
            <>
              <CheckCircle className="h-3.5 w-3.5 text-green-500" />
              {completeSources.length} source
              {completeSources.length !== 1 && "s"} &middot;{" "}
              {totalPapers.toLocaleString()} papers fetched
              {errorCount > 0 && (
                <span className="text-red-400">
                  &middot; {errorCount} failed
                </span>
              )}
            </>
          )}
        </span>
        {expanded ? (
          <ChevronUp className="h-3.5 w-3.5 text-text-muted" />
        ) : (
          <ChevronDown className="h-3.5 w-3.5 text-text-muted" />
        )}
      </button>

      {/* Animated collapsible body */}
      <div
        className="grid transition-[grid-template-rows] duration-300 ease-out"
        style={{ gridTemplateRows: expanded ? "1fr" : "0fr" }}
      >
        <div className="overflow-hidden">
          <div className="px-4 pb-3 pt-2 border-t border-border space-y-0.5">
            {/* ---- Source rows ---- */}
            {sources.map((node) => (
              <div
                key={node.source}
                className={`flex items-center justify-between gap-3 py-0.5 text-xs transition-opacity duration-200 ${
                  node.status === "complete" && isStreaming
                    ? "opacity-50"
                    : "opacity-100"
                }`}
              >
                <span className="flex items-center gap-2 shrink-0">
                  <SourceIcon status={node.status} />
                  <span
                    className={
                      node.status === "error"
                        ? "text-red-400"
                        : "text-text-secondary"
                    }
                  >
                    {node.source}
                  </span>
                </span>
                <SourceDetail node={node} />
              </div>
            ))}

            {/* ---- Phase section (scoring + filtering chain-of-thought) ---- */}
            {phases.length > 0 && (
              <div className="mt-1.5 pt-1.5 border-t border-dashed border-border/50 space-y-1">
                {phases.map((node) => (
                  <div
                    key={node.phase}
                    className="flex items-start gap-2 text-xs"
                  >
                    <div className="mt-0.5 shrink-0">
                      <PhaseIcon status={node.status} />
                    </div>
                    <div className="flex flex-col min-w-0">
                      {node.phase === "scoring" && (
                        <ScoringContent node={node} />
                      )}
                      {node.phase === "filtering" && (
                        <FilteringContent node={node} />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
