import { cn } from "@/lib/utils";

interface SpinnerProps {
  className?: string;
  size?: "sm" | "md" | "lg";
}

const SIZES = {
  sm: "h-4 w-4 border-2",
  md: "h-10 w-10 border-2",
  lg: "h-12 w-12 border-2",
} as const;

export default function Spinner({ className, size = "md" }: SpinnerProps) {
  return (
    <div
      className={cn(
        "animate-spin rounded-full border-b-indigo-600",
        SIZES[size],
        className,
      )}
    />
  );
}
