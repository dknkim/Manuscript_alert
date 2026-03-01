"use client";

import { useState, useEffect } from "react";
import {
  listModels,
  saveModel,
  loadModel,
  previewModel,
  deleteModel,
  saveSettings,
} from "@/lib/api";
import type { Settings, ModelInfo, FlashMessage } from "@/types";

interface ModelsTabProps {
  settings: Settings;
  onSettingsChange: () => Promise<void>;
}

export default function ModelsTab({
  settings,
  onSettingsChange,
}: ModelsTabProps) {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [modelName, setModelName] = useState<string>("");
  const [previewData, setPreviewData] = useState<Settings | null>(null);
  const [previewName, setPreviewName] = useState<string>("");
  const [msg, setMsg] = useState<FlashMessage | null>(null);

  const refresh = async (): Promise<void> => {
    try {
      const data = await listModels();
      setModels(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const flash = (text: string, type: "success" | "error" = "success"): void => {
    setMsg({ text, type });
    setTimeout(() => setMsg(null), 4000);
  };

  const handleSave = async (): Promise<void> => {
    if (!modelName.trim()) {
      flash("Please enter a model name.", "error");
      return;
    }
    try {
      await saveModel(modelName.trim());
      flash(`Model "${modelName}" saved.`);
      setModelName("");
      refresh();
    } catch (e: unknown) {
      flash(e instanceof Error ? e.message : "Unknown error", "error");
    }
  };

  const handleLoad = async (filename: string): Promise<void> => {
    try {
      await loadModel(filename);
      flash("Model loaded successfully.");
      onSettingsChange();
    } catch (e: unknown) {
      flash(e instanceof Error ? e.message : "Unknown error", "error");
    }
  };

  const handlePreview = async (
    filename: string,
    name: string,
  ): Promise<void> => {
    try {
      const data = await previewModel(filename);
      setPreviewData(data);
      setPreviewName(name);
    } catch (e: unknown) {
      flash(e instanceof Error ? e.message : "Unknown error", "error");
    }
  };

  const handleDelete = async (filename: string): Promise<void> => {
    if (!window.confirm("Are you sure you want to delete this model?")) return;
    try {
      await deleteModel(filename);
      flash("Model deleted.");
      refresh();
    } catch (e: unknown) {
      flash(e instanceof Error ? e.message : "Unknown error", "error");
    }
  };

  const handleExport = (): void => {
    const json = JSON.stringify(settings, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `manuscript_alert_settings_${new Date()
      .toISOString()
      .slice(0, 19)
      .replace(/[:-]/g, "")}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleImport = async (
    e: React.ChangeEvent<HTMLInputElement>,
  ): Promise<void> => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const imported = JSON.parse(text) as Settings;
      await saveSettings(imported);
      flash("Settings imported successfully.");
      onSettingsChange();
    } catch (err: unknown) {
      flash(
        "Failed to import settings: " +
          (err instanceof Error ? err.message : "Unknown error"),
        "error",
      );
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <div>
        <h2 className="text-xl font-bold text-text-primary">
          🤖 Model Management
        </h2>
        <p className="text-sm text-text-muted mt-1">
          Save and manage different configuration presets for different research
          scenarios.
        </p>
      </div>

      {/* Flash message */}
      {msg && (
        <div
          className={`px-4 py-3 rounded-lg text-sm ${
            msg.type === "error"
              ? "bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300"
              : "bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-300"
          }`}
        >
          {msg.text}
        </div>
      )}

      {/* Save new model */}
      <div className="bg-surface-raised rounded-xl border border-border p-5">
        <h3 className="text-sm font-semibold text-text-primary mb-3">
          Save Current Settings as Model
        </h3>
        <div className="flex gap-3">
          <input
            type="text"
            value={modelName}
            onChange={(e) => setModelName(e.target.value)}
            placeholder='e.g., "AD Neuroimaging Focus"'
            className="flex-1 px-3 py-2 border border-border bg-surface rounded-lg text-sm text-text-primary focus:ring-2 focus:ring-accent focus:border-accent outline-hidden"
          />
          <button
            onClick={handleSave}
            className="px-5 py-2 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm font-semibold transition-colors"
          >
            💾 Save
          </button>
        </div>
      </div>

      {/* Existing models */}
      <div className="bg-surface-raised rounded-xl border border-border p-5">
        <h3 className="text-sm font-semibold text-text-primary mb-3">
          Load Existing Models
          <span className="ml-2 text-text-muted font-normal">
            ({models.length})
          </span>
        </h3>

        {models.length === 0 ? (
          <p className="text-sm text-text-muted py-4 text-center">
            No saved models yet. Save your current settings to get started.
          </p>
        ) : (
          <div className="divide-y divide-border">
            {models.map((m) => (
              <div
                key={m.filename}
                className="flex items-center justify-between py-3"
              >
                <div>
                  <p className="text-sm font-medium text-text-primary">{m.name}</p>
                  <p className="text-xs text-text-muted">
                    Modified: {m.modified}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Btn onClick={() => handleLoad(m.filename)} color="indigo">
                    Load
                  </Btn>
                  <Btn
                    onClick={() => handlePreview(m.filename, m.name)}
                    color="gray"
                  >
                    Preview
                  </Btn>
                  <Btn onClick={() => handleDelete(m.filename)} color="red">
                    Delete
                  </Btn>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Preview modal */}
      {previewData && (
        <div className="bg-surface-raised rounded-xl border border-border p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-text-primary">
              Preview: {previewName}
            </h3>
            <button
              onClick={() => setPreviewData(null)}
              className="text-text-muted hover:text-text-secondary"
            >
              ✕
            </button>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="font-medium text-text-secondary mb-1">Keywords</p>
              <p className="text-text-muted">
                {(previewData.keywords || []).length} keywords:{" "}
                {(previewData.keywords || []).slice(0, 5).join(", ")}
                {(previewData.keywords || []).length > 5 ? "…" : ""}
              </p>
            </div>
            <div>
              <p className="font-medium text-text-secondary mb-1">
                Journal Exclusions
              </p>
              <p className="text-text-muted">
                {(previewData.journal_exclusions || []).length} patterns
              </p>
            </div>
            <div>
              <p className="font-medium text-text-secondary mb-1">Search Settings</p>
              <p className="text-text-muted">
                Days back:{" "}
                {previewData.search_settings?.days_back || "N/A"} | Mode:{" "}
                {previewData.search_settings?.search_mode || "N/A"}
              </p>
            </div>
            <div>
              <p className="font-medium text-text-secondary mb-1">Target Journals</p>
              <p className="text-text-muted">
                {(previewData.target_journals?.exact_matches || [])
                  .slice(0, 3)
                  .join(", ")}
                {(previewData.target_journals?.exact_matches || []).length > 3
                  ? "…"
                  : ""}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-surface-raised rounded-xl border border-border p-5">
        <h3 className="text-sm font-semibold text-text-primary mb-3">
          Quick Actions
        </h3>
        <div className="flex gap-3">
          <button
            onClick={handleExport}
            className="px-4 py-2 border border-border rounded-lg text-sm font-medium text-text-secondary hover:bg-surface-inset transition-colors"
          >
            📋 Export Settings JSON
          </button>
          <label className="px-4 py-2 border border-border rounded-lg text-sm font-medium text-text-secondary hover:bg-surface-inset transition-colors cursor-pointer">
            📤 Import Settings
            <input
              type="file"
              accept=".json"
              onChange={handleImport}
              className="hidden"
            />
          </label>
        </div>
      </div>
    </div>
  );
}

/* ── Sub-components ──────────────────────────────────────── */

function Btn({
  children,
  onClick,
  color,
}: {
  children: React.ReactNode;
  onClick: () => void;
  color: "indigo" | "gray" | "red";
}) {
  const colors: Record<string, string> = {
    indigo: "bg-accent-subtle text-accent-text hover:bg-accent-subtle/80",
    gray: "bg-surface-inset text-text-secondary hover:bg-surface-inset/80",
    red: "bg-red-50 dark:bg-red-950 text-red-700 dark:text-red-300 hover:bg-red-100 dark:hover:bg-red-900",
  };
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${colors[color]}`}
    >
      {children}
    </button>
  );
}
