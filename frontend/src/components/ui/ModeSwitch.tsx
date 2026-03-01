import { cn } from "@/lib/utils";

type Mode = "classic" | "agent";

interface ModeSwitchProps {
  mode: Mode;
  onChange: (mode: Mode) => void;
}

export default function ModeSwitch({ mode, onChange }: ModeSwitchProps) {
  return (
    <div className="grid grid-cols-2 gap-1 bg-surface-inset rounded-lg p-1">
      <button
        onClick={() => onChange("classic")}
        className={cn(
          "py-1.5 rounded-md text-xs font-medium transition-all",
          mode === "classic"
            ? "bg-surface-raised text-text-primary shadow-xs"
            : "text-text-muted hover:text-text-secondary",
        )}
      >
        Classic
      </button>
      <button
        disabled
        className="py-1.5 rounded-md text-xs font-medium text-text-muted/50 cursor-not-allowed"
        title="Coming soon"
      >
        Agent
      </button>
    </div>
  );
}
