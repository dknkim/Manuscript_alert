"use client";

import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface MobileDrawerProps {
  side: "left" | "right";
  open: boolean;
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}

// 73px header matches SearchPanel/DashboardPanel's `top-[73px]` offset,
// so their `h-[calc(100vh-73px)]` fits the flex-1 scroll area exactly.
export default function MobileDrawer({ side, open, title, onClose, children }: MobileDrawerProps) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div
        className={cn(
          "absolute top-0 h-full w-72 bg-surface-raised flex flex-col z-10",
          side === "left" ? "left-0" : "right-0",
        )}
      >
        <div className="h-[73px] flex items-center justify-between px-4 border-b border-border shrink-0">
          <span className="text-sm font-semibold text-text-primary">{title}</span>
          <button
            onClick={onClose}
            className="p-2 rounded-md hover:bg-surface-inset transition-colors"
            aria-label="Close"
          >
            <X className="h-4 w-4 text-text-secondary" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {children}
        </div>
      </div>
    </div>
  );
}
