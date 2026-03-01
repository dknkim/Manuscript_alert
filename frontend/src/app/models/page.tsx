"use client";

import { useSettings } from "@/hooks/useSettings";
import ModelsTab from "@/components/ModelsTab";
import Spinner from "@/components/ui/Spinner";

export default function ModelsPage() {
  const { settings, reload } = useSettings();

  if (!settings) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Spinner size="lg" />
      </div>
    );
  }

  return <ModelsTab settings={settings} onSettingsChange={reload} />;
}
