"use client";

import { useState, useEffect, useCallback } from "react";
import { getSettings } from "@/lib/api";
import type { Settings, FetchResult } from "@/types";
import PapersTab from "@/components/PapersTab";
import ModelsTab from "@/components/ModelsTab";
import SettingsTab from "@/components/SettingsTab";

interface TabDef {
  key: string;
  label: string;
  icon: string;
}

const TABS: TabDef[] = [
  { key: "papers", label: "Papers", icon: "📚" },
  { key: "models", label: "Models", icon: "🤖" },
  { key: "settings", label: "Settings", icon: "⚙️" },
];

export default function Home() {
  const [activeTab, setActiveTab] = useState<string>("papers");
  const [settings, setSettings] = useState<Settings | null>(null);

  // Lifted paper state — survives tab switches
  const [papersResult, setPapersResult] = useState<FetchResult | null>(null);
  const [papersLoading, setPapersLoading] = useState<boolean>(false);
  const [papersError, setPapersError] = useState<string | null>(null);

  const loadSettings = useCallback(async () => {
    try {
      const data = await getSettings();
      setSettings(data);
    } catch (err) {
      console.error("Failed to load settings:", err);
    }
  }, []);

  // Reload settings AND clear papers (e.g. after saving settings or loading a model)
  const handleSettingsChange = useCallback(async () => {
    await loadSettings();
    setPapersResult(null); // clear stale papers so they re-fetch with new config
  }, [loadSettings]);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  if (!settings) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-30">
        <div className="max-w-[1440px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Manuscript Alert System
              </h1>
              <p className="text-sm text-gray-500 mt-0.5">
                Stay updated with the latest PubMed, arXiv, bioRxiv, and
                medRxiv papers
              </p>
            </div>
            {/* Tab navigation */}
            <nav className="flex gap-1 bg-gray-100 rounded-lg p-1">
              {TABS.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                    activeTab === tab.key
                      ? "bg-white text-gray-900 shadow-sm"
                      : "text-gray-600 hover:text-gray-900"
                  }`}
                >
                  <span className="mr-1.5">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>
      </header>

      {/* Content — all tabs stay mounted, only visibility toggles */}
      <main className="max-w-[1440px] mx-auto">
        <div style={{ display: activeTab === "papers" ? "block" : "none" }}>
          <PapersTab
            settings={settings}
            result={papersResult}
            setResult={setPapersResult}
            loading={papersLoading}
            setLoading={setPapersLoading}
            error={papersError}
            setError={setPapersError}
          />
        </div>
        <div style={{ display: activeTab === "models" ? "block" : "none" }}>
          <ModelsTab
            settings={settings}
            onSettingsChange={handleSettingsChange}
          />
        </div>
        <div style={{ display: activeTab === "settings" ? "block" : "none" }}>
          <SettingsTab
            settings={settings}
            onSettingsChange={handleSettingsChange}
          />
        </div>
      </main>
    </div>
  );
}
