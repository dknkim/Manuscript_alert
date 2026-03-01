import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import AppShell from "@/components/layout/AppShell";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Manuscript Alert System",
  description:
    "Stay updated with the latest PubMed, arXiv, bioRxiv, and medRxiv papers",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${inter.className} bg-surface text-text-primary antialiased`}
      >
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
