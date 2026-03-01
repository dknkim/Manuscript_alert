"use client";

import { Activity } from "lucide-react";

export default function AgentActivityStream() {
  return (
    <div className="p-4 border border-dashed border-gray-200 rounded-lg text-center text-gray-400">
      <Activity className="h-5 w-5 mx-auto mb-2" />
      <p className="text-xs">
        Agent activity will appear here when agent mode is enabled (Step 6).
      </p>
    </div>
  );
}
