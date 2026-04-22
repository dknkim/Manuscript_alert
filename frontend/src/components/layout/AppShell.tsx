"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { FileText, Settings, Database, BookOpen, Moon, Sun } from "lucide-react";
import { useAuth, UserButton } from "@clerk/nextjs";
import { cn } from "@/lib/utils";

const hasClerk = !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

const NAV_ITEMS: { href: string; label: string; icon: React.ElementType }[] = [
  { href: "/", label: "Papers", icon: FileText },
  { href: "/models", label: "Models", icon: Database },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/kb", label: "Knowledge Base", icon: BookOpen },
];

/** Only mounted when ClerkProvider is present — safe to call useAuth() here. */
function UserAvatar() {
  const { isSignedIn } = useAuth();
  if (!isSignedIn) return null;
  return <UserButton />;
}

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
              <h1 className="text-xl lg:text-2xl font-bold text-text-primary tracking-tight">
                Manuscript Alert
              </h1>
              <p className="hidden lg:block text-sm text-text-muted mt-0.5">
                Research paper monitoring across PubMed, arXiv, bioRxiv &amp;
                medRxiv
              </p>
            </div>
            <div className="flex items-center gap-3">
              <nav className="hidden lg:flex gap-1 bg-surface-inset rounded-lg p-1">
                {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
                  const active =
                    href === "/"
                      ? pathname === "/"
                      : pathname.startsWith(href);
                  return (
                    <Link
                      key={href}
                      href={href}
                      className={cn(
                        "flex items-center gap-1.5 px-4 py-2 rounded-md text-sm font-medium transition-all",
                        active
                          ? "bg-surface-raised text-text-primary shadow-xs"
                          : "text-text-secondary hover:text-text-primary",
                      )}
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
              {hasClerk && <UserAvatar />}
            </div>
          </div>
        </div>
      </header>
      {/* Bottom tab bar — mobile only */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-surface-raised border-t border-border">
        <div className="flex justify-around py-1">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
            const shortLabel = href === "/kb" ? "KB" : label;
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex flex-col items-center gap-0.5 px-4 py-2 text-xs font-medium transition-colors",
                  active ? "text-accent" : "text-text-secondary",
                )}
              >
                <Icon className="h-5 w-5" />
                {shortLabel}
              </Link>
            );
          })}
        </div>
      </nav>

      <main className="max-w-[1440px] mx-auto pb-16 lg:pb-0">{children}</main>
    </div>
  );
}
