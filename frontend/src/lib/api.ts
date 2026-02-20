import type {
  Settings,
  FetchResult,
  DataSources,
  ModelInfo,
  BackupInfo,
  ArchiveResponse,
  Paper,
} from "@/types";

const BASE: string = process.env.NEXT_PUBLIC_API_URL || "/api";

/* ── helpers ──────────────────────────────────────────────── */

async function request(
  url: string,
  options: RequestInit = {},
): Promise<Response> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res;
}

/* ── Settings ─────────────────────────────────────────────── */

export async function getSettings(): Promise<Settings> {
  const res = await request("/settings");
  return res.json();
}

export async function saveSettings(
  settings: Settings,
): Promise<{ status: string }> {
  const res = await request("/settings", {
    method: "PUT",
    body: JSON.stringify({ settings }),
  });
  return res.json();
}

/* ── Papers ───────────────────────────────────────────────── */

export async function fetchPapers(
  dataSources: DataSources,
  searchMode: string,
): Promise<FetchResult> {
  const res = await request("/papers/fetch", {
    method: "POST",
    body: JSON.stringify({
      data_sources: dataSources,
      search_mode: searchMode,
    }),
  });
  return res.json();
}

export async function exportPapersCSV(
  dataSources: DataSources,
  searchMode: string,
): Promise<Blob> {
  const res = await fetch(`${BASE}/papers/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      data_sources: dataSources,
      search_mode: searchMode,
    }),
  });
  return res.blob();
}

/* ── Models ───────────────────────────────────────────────── */

export async function listModels(): Promise<ModelInfo[]> {
  const res = await request("/models");
  return res.json();
}

export async function saveModel(
  name: string,
): Promise<{ status: string; filename: string }> {
  const res = await request("/models", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  return res.json();
}

export async function loadModel(
  filename: string,
): Promise<{ status: string }> {
  const res = await request(`/models/${filename}/load`, { method: "POST" });
  return res.json();
}

export async function previewModel(
  filename: string,
): Promise<Settings> {
  const res = await request(`/models/${filename}/preview`);
  return res.json();
}

export async function deleteModel(
  filename: string,
): Promise<{ status: string }> {
  const res = await request(`/models/${filename}`, { method: "DELETE" });
  return res.json();
}

/* ── Backups ──────────────────────────────────────────────── */

export async function listBackups(): Promise<BackupInfo[]> {
  const res = await request("/backups");
  return res.json();
}

export async function restoreBackup(
  path: string,
): Promise<{ status: string }> {
  const res = await request("/backups/restore", {
    method: "POST",
    body: JSON.stringify({ path }),
  });
  return res.json();
}

export async function createBackup(): Promise<{ status: string }> {
  const res = await request("/backups/create", { method: "POST" });
  return res.json();
}

/* ── Archive ─────────────────────────────────────────────── */

export async function archivePaper(
  paper: Paper,
): Promise<{ status: string }> {
  const res = await request("/papers/archive", {
    method: "POST",
    body: JSON.stringify({ paper }),
  });
  return res.json();
}

export async function getArchivedPapers(): Promise<ArchiveResponse> {
  const res = await request("/papers/archive");
  return res.json();
}

export async function unarchivePaper(
  title: string,
  date: string,
): Promise<{ status: string }> {
  const res = await request("/papers/archive", {
    method: "DELETE",
    body: JSON.stringify({ title, date }),
  });
  return res.json();
}
