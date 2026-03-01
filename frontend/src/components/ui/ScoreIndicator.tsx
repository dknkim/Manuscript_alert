import { cn } from "@/lib/utils";

const SCORE_TIERS = [
  { min: 7.5, text: "text-green-600 dark:text-green-400", border: "border-green-500", borderL: "border-l-green-500" },
  { min: 5, text: "text-amber-500 dark:text-amber-400", border: "border-amber-400", borderL: "border-l-amber-400" },
  { min: 2.5, text: "text-orange-600 dark:text-orange-400", border: "border-orange-400", borderL: "border-l-orange-400" },
  { min: -Infinity, text: "text-red-600 dark:text-red-400", border: "border-red-500", borderL: "border-l-red-500" },
] as const;

function tierFor(score: number) {
  return SCORE_TIERS.find((t) => score >= t.min)!;
}

/** Border-l color class for card left-border accent. */
export function scoreAccentBorder(score: number): string {
  return tierFor(score).borderL;
}

interface ScoreIndicatorProps {
  score: number;
  className?: string;
}

export default function ScoreIndicator({
  score,
  className,
}: ScoreIndicatorProps) {
  const tier = tierFor(score);
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center border-2 rounded-xl px-3 py-2",
        tier.border,
        className,
      )}
      aria-label={`Score: ${score.toFixed(1)}`}
    >
      <span className={cn("text-lg font-bold leading-none", tier.text)}>
        {score.toFixed(1)}
      </span>
      <span className="text-[10px] text-text-muted font-medium">Score</span>
    </div>
  );
}
