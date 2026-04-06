import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";
import AppShell from "@/components/layout/AppShell";
import { ClerkTokenProvider } from "@/components/ClerkTokenProvider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Manuscript Alert System",
  description:
    "Stay updated with the latest PubMed, arXiv, bioRxiv, and medRxiv papers",
};

const CLERK_KEY = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

/** Inner HTML structure — defined once, conditionally wrapped by ClerkProvider. */
function RootContent({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${inter.className} bg-surface text-text-primary antialiased`}
      >
        {/* Registers Clerk token getter with the API client (no-op without Clerk) */}
        {CLERK_KEY && <ClerkTokenProvider />}
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  if (CLERK_KEY) {
    return (
      <ClerkProvider publishableKey={CLERK_KEY} afterSignOutUrl="/sign-in">
        <RootContent>{children}</RootContent>
      </ClerkProvider>
    );
  }
  // No Clerk configured — local dev without auth
  return <RootContent>{children}</RootContent>;
}
