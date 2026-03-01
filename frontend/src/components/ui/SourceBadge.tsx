import { cn } from "@/lib/utils";

const SOURCE_COLORS: Record<string, string> = {
  PubMed: "bg-orange-500",
  arXiv: "bg-red-700",
  BioRxiv: "bg-emerald-600",
  Biorxiv: "bg-emerald-600",
  MedRxiv: "bg-blue-600",
  Medrxiv: "bg-blue-600",
};

interface SourceBadgeProps {
  source: string;
  className?: string;
}

export default function SourceBadge({ source, className }: SourceBadgeProps) {
  const color = SOURCE_COLORS[source] || "bg-gray-500";
  return (
    <span
      className={cn(
        "inline-block px-3 py-1 rounded-full text-xs font-bold text-white",
        color,
        className,
      )}
    >
      {source}
    </span>
  );
}
