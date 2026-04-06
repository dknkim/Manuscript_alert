import type {
  Settings,
  FetchResult,
  DataSources,
  ModelInfo,
  BackupInfo,
  ArchiveResponse,
  Paper,
} from "@/types";

const BASE: string = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

/* ── Auth token injection ─────────────────────────────────── */

type TokenGetter = () => Promise<string | null>;
let _getToken: TokenGetter | null = null;

// Resolves when ClerkTokenProvider registers the getter (i.e. Clerk is loaded).
// API calls wait on this so they never fire before the token is available.
let _clerkReady: Promise<void>;
let _clerkReadyResolve: (() => void) | null = null;
_clerkReady = new Promise<void>((res) => { _clerkReadyResolve = res; });

/** Called once by ClerkTokenProvider after Clerk initializes. */
export function initClerkTokenGetter(fn: TokenGetter) {
  _getToken = fn;
  _clerkReadyResolve?.();
}

/** Returns the current Clerk JWT, or null if auth is not configured. */
export async function getAuthToken(): Promise<string | null> {
  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) return null;
  // Wait for Clerk to initialize (typically <300 ms), with a 5 s safety timeout.
  await Promise.race([_clerkReady, new Promise<void>((r) => setTimeout(r, 5000))]);
  return _getToken ? _getToken() : null;
}

/* ── helpers ──────────────────────────────────────────────── */

async function request(
  url: string,
  options: RequestInit = {},
): Promise<Response> {
  const token = await getAuthToken();
  const res = await fetch(`${BASE}${url}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers as Record<string, string>),
    },
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
