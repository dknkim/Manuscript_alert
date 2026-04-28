"use client";

import React, { useState, useEffect } from "react";
import {
  Save,
  Play,
  Search,
  Trash2,
  Download,
  Upload,
  X,
  Bot,
} from "lucide-react";
import {
  listModels,
  saveModel,
  loadModel,
  previewModel,
  deleteModel,
  saveSettings,
} from "@/lib/api";
import type { Settings, ModelInfo, FlashMessage } from "@/types";
import { persistActiveSlot, slotKeyFromFilename } from "@/hooks/useModelSlots";

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
      await persistActiveSlot(slotKeyFromFilename(filename));
      flash("Model loaded successfully.");
      await onSettingsChange();
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
      await persistActiveSlot(null);
      flash("Settings imported successfully.");
      await onSettingsChange();
    } catch (err: unknown) {
      flash(
        "Failed to import settings: " +
          (err instanceof Error ? err.message : "Unknown error"),
        "error",
      );
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6 space-y-8">
      <div>
        <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
          <Bot className="w-5 h-5" /> Model Management
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
            className="px-4 py-2 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm font-semibold transition-colors flex items-center gap-1.5"
          >
            <Save className="w-4 h-4" />
            <span className="hidden sm:inline">Save</span>
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
                  <Btn onClick={() => handleLoad(m.filename)} color="indigo" icon={<Play className="w-3.5 h-3.5" />} label="Load" />
                  <Btn onClick={() => handlePreview(m.filename, m.name)} color="gray" icon={<Search className="w-3.5 h-3.5" />} label="Preview" />
                  <Btn onClick={() => handleDelete(m.filename)} color="red" icon={<Trash2 className="w-3.5 h-3.5" />} label="Delete" />
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
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
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

      {/* Settings Backup */}
      <div className="bg-surface-raised rounded-xl border border-border p-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-text-primary">
              Settings Backup
            </h3>
            <p className="text-xs text-text-muted mt-0.5 hidden sm:block">
              Export or restore settings as JSON.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleExport}
              title="Export Settings"
              className="px-3 py-1.5 border border-border rounded-md text-xs font-medium text-text-secondary hover:bg-surface-inset transition-colors flex items-center gap-1.5"
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Export</span>
            </button>
            <label
              title="Import Settings"
              className="px-3 py-1.5 border border-border rounded-md text-xs font-medium text-text-secondary hover:bg-surface-inset transition-colors cursor-pointer flex items-center gap-1.5"
            >
              <Upload className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Import</span>
              <input type="file" accept=".json" onChange={handleImport} className="hidden" />
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Sub-components ──────────────────────────────────────── */

function Btn({
  onClick,
  color,
  icon,
  label,
}: {
  onClick: () => void;
  color: "indigo" | "gray" | "red";
  icon: React.ReactNode;
  label: string;
}) {
  const colors: Record<string, string> = {
    indigo: "bg-accent-subtle text-accent-text hover:bg-accent-subtle/80",
    gray: "bg-surface-inset text-text-secondary hover:bg-surface-inset/80",
    red: "bg-red-50 dark:bg-red-950 text-red-700 dark:text-red-300 hover:bg-red-100 dark:hover:bg-red-900",
  };
  return (
    <button
      onClick={onClick}
      title={label}
      className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5 ${colors[color]}`}
    >
      {icon}
      <span className="hidden sm:inline">{label}</span>
    </button>
  );
}
