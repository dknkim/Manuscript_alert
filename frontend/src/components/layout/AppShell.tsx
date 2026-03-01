"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { FileText, Settings, Database, BookOpen, Moon, Sun } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/", label: "Papers", icon: FileText },
  { href: "/models", label: "Models", icon: Database },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/kb", label: "Knowledge Base", icon: BookOpen, disabled: true },
] as const;

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [dark, setDark] = useState(false);

  // Initialize from system preference
  useEffect(() => {
    const stored = localStorage.getItem("theme");
    if (stored === "dark" || (!stored && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
      setDark(true);
      document.documentElement.classList.add("dark");
    }
  }, []);

  const toggleTheme = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("theme", next ? "dark" : "light");
  };

  return (
    <div className="min-h-screen bg-surface">
      <header className="bg-surface-raised border-b border-border sticky top-0 z-30">
        <div className="max-w-[1440px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-text-primary tracking-tight">
                Manuscript Alert
              </h1>
              <p className="text-sm text-text-muted mt-0.5">
                Research paper monitoring across PubMed, arXiv, bioRxiv &amp;
                medRxiv
              </p>
            </div>
            <div className="flex items-center gap-3">
              <nav className="flex gap-1 bg-surface-inset rounded-lg p-1">
                {NAV_ITEMS.map(({ href, label, icon: Icon, ...rest }) => {
                  const isDisabled = "disabled" in rest && rest.disabled;
                  const active =
                    href === "/"
                      ? pathname === "/"
                      : pathname.startsWith(href);
                  return (
                    <Link
                      key={href}
                      href={isDisabled ? "#" : href}
                      onClick={isDisabled ? (e) => e.preventDefault() : undefined}
                      className={cn(
                        "flex items-center gap-1.5 px-4 py-2 rounded-md text-sm font-medium transition-all",
                        active
                          ? "bg-surface-raised text-text-primary shadow-xs"
                          : "text-text-secondary hover:text-text-primary",
                        isDisabled && "opacity-50 cursor-not-allowed hover:text-text-secondary",
                      )}
                      tabIndex={isDisabled ? -1 : undefined}
                      aria-disabled={isDisabled || undefined}
                      title={isDisabled ? "Coming soon" : undefined}
                    >
                      <Icon className="h-4 w-4" />
                      {label}
                    </Link>
                  );
                })}
              </nav>
              <button
                onClick={toggleTheme}
                className="p-2 rounded-md text-text-secondary hover:text-text-primary hover:bg-surface-inset transition-colors"
                title={dark ? "Switch to light mode" : "Switch to dark mode"}
              >
                {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              </button>
            </div>
          </div>
        </div>
      </header>
      <main className="max-w-[1440px] mx-auto">{children}</main>
    </div>
  );
}
