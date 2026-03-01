import { useState, useCallback, useRef } from "react";
import {
  fetchEventSource,
  EventStreamContentType,
} from "@microsoft/fetch-event-source";
import type { DataSources, FetchResult } from "@/types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

// ---------------------------------------------------------------------------
// Display state — structured model derived from raw SSE events.
// The component renders this directly. No flat step array, no ordering bugs.
// ---------------------------------------------------------------------------

export interface SourceNode {
  source: string;
  status: "fetching" | "complete" | "error";
  papersFound?: number;
  /** Batch progress (PubMed only) — inline metadata, not a separate row. */
  batch?: number;
  totalBatches?: number;
  papersSoFar?: number;
  errorMessage?: string;
}

export interface PhaseNode {
  phase: "scoring" | "filtering";
  status: "active" | "done";
  /** Scoring fields */
  totalPapers?: number;
  criteria?: string[];
  /** Filtering fields */
  totalBefore?: number;
  totalAfter?: number;
  minKeywords?: number;
  mustHaveKeywords?: string[];
}

export interface DisplayState {
  sources: SourceNode[];
  phases: PhaseNode[];
}

interface UseAgentStreamReturn {
  displayState: DisplayState;
  isStreaming: boolean;
  result: FetchResult | null;
  error: string | null;
  startStream: (dataSources: DataSources, searchMode: string) => void;
  reset: () => void;
}

const EMPTY_DISPLAY: DisplayState = { sources: [], phases: [] };

/** Update or insert a source node, preserving insertion order. */
function upsertSource(
  sources: SourceNode[],
  name: string,
  updater: (existing: SourceNode | undefined) => SourceNode,
): SourceNode[] {
  const idx = sources.findIndex((s) => s.source === name);
  if (idx !== -1) {
    const next = [...sources];
    next[idx] = updater(sources[idx]);
    return next;
  }
  return [...sources, updater(undefined)];
}

export function useAgentStream(): UseAgentStreamReturn {
  const [display, setDisplay] = useState<DisplayState>(EMPTY_DISPLAY);
  const [isStreaming, setIsStreaming] = useState(false);
  const [result, setResult] = useState<FetchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setDisplay(EMPTY_DISPLAY);
    setIsStreaming(false);
    setResult(null);
    setError(null);
  }, []);

  const startStream = useCallback(
    (dataSources: DataSources, searchMode: string) => {
      reset();
      setIsStreaming(true);

      const ctrl = new AbortController();
      abortRef.current = ctrl;

      fetchEventSource(`${BASE}/papers/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          data_sources: dataSources,
          search_mode: searchMode,
        }),
        signal: ctrl.signal,
        openWhenHidden: true,

        async onopen(response) {
          if (
            response.ok &&
            response.headers.get("content-type")?.includes(EventStreamContentType)
          ) {
            return;
          }
          throw new Error(`SSE connection failed: ${response.status}`);
        },

        onmessage(msg) {
          if (!msg.event || !msg.data) return;
          if (ctrl.signal.aborted) return;
          const data = JSON.parse(msg.data);

          switch (msg.event) {
            case "source_start":
              setDisplay((prev) => ({
                ...prev,
                sources: upsertSource(prev.sources, data.source, () => ({
                  source: data.source,
                  status: "fetching",
                })),
              }));
              break;

            case "batch_progress":
              setDisplay((prev) => ({
                ...prev,
                sources: upsertSource(
                  prev.sources,
                  data.source,
                  (existing) => ({
                    ...(existing || { source: data.source }),
                    status: "fetching" as const,
                    batch: data.batch,
                    totalBatches: data.total,
                    papersSoFar: data.papers_so_far,
                  }),
                ),
              }));
              break;

            case "source_complete":
              setDisplay((prev) => ({
                ...prev,
                sources: upsertSource(prev.sources, data.source, () => ({
                  source: data.source,
                  status: "complete",
                  papersFound: data.count,
                })),
              }));
              break;

            case "source_error":
              setDisplay((prev) => ({
                ...prev,
                sources: upsertSource(prev.sources, data.source, () => ({
                  source: data.source,
                  status: "error",
                  errorMessage: data.error,
                })),
              }));
              break;

            case "scoring":
              setDisplay((prev) => ({
                ...prev,
                phases: [
                  {
                    phase: "scoring",
                    status: "active",
                    totalPapers: data.total_papers,
                    criteria: data.criteria,
                  },
                ],
              }));
              break;

            case "filtering":
              setDisplay((prev) => ({
                ...prev,
                phases: [
                  // Mark scoring as done
                  ...prev.phases.map((p) =>
                    p.phase === "scoring"
                      ? { ...p, status: "done" as const }
                      : p,
                  ),
                  // Append filtering as done
                  {
                    phase: "filtering" as const,
                    status: "done" as const,
                    totalBefore: data.total_before,
                    totalAfter: data.total_after,
                    minKeywords: data.min_keywords,
                    mustHaveKeywords: data.must_have_keywords,
                  },
                ],
              }));
              break;

            case "complete":
              // Don't add a display row — the phase section already shows
              // scoring + filtering. Just deliver the result and stop.
              setResult(data as FetchResult);
              setIsStreaming(false);
              ctrl.abort();
              break;
          }
        },

        onerror(err) {
          if (ctrl.signal.aborted) return;
          setError(err instanceof Error ? err.message : "Stream error");
          setIsStreaming(false);
          throw err; // stop retrying
        },

        onclose() {
          setIsStreaming(false);
          throw new Error("done"); // prevent fetchEventSource from retrying
        },
      });
    },
    [reset],
  );

  return { displayState: display, isStreaming, result, error, startStream, reset };
}
