"use client";

import { useSettings } from "@/hooks/useSettings";
import SettingsTab from "@/components/SettingsTab";
import Spinner from "@/components/ui/Spinner";

export default function SettingsPage() {
  const { settings, loading, error, reload } = useSettings();

  if (loading && !settings) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] px-6">
        <div className="max-w-md w-full rounded-xl border border-border bg-surface-raised p-6 text-center">
          <h2 className="text-lg font-semibold text-text-primary">
            Failed to load settings
          </h2>
          <p className="mt-2 text-sm text-text-muted">
            {error || "The API did not return settings in time."}
          </p>
          <button
            onClick={() => void reload()}
            className="mt-4 inline-flex items-center justify-center rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-accent-hover"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return <SettingsTab settings={settings} onSettingsChange={reload} />;
}
