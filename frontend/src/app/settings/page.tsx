"use client";

import { useSettings } from "@/hooks/useSettings";
import SettingsTab from "@/components/SettingsTab";
import Spinner from "@/components/ui/Spinner";

export default function SettingsPage() {
  const { settings, reload } = useSettings();

  if (!settings) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Spinner size="lg" />
      </div>
    );
  }

  return <SettingsTab settings={settings} onSettingsChange={reload} />;
}
