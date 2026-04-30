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
let _isClerkReady = false;

// Resolves when ClerkTokenProvider registers the getter (i.e. Clerk is loaded).
// API calls wait on this so they never fire before the token is available.
let _clerkReady: Promise<void>;
let _clerkReadyResolve: (() => void) | null = null;
_clerkReady = new Promise<void>((res) => { _clerkReadyResolve = res; });

/** Called once by ClerkTokenProvider after Clerk initializes. */
export function initClerkTokenGetter(fn: TokenGetter) {
  _getToken = fn;
  _isClerkReady = true;
  _clerkReadyResolve?.();
}

export async function waitForClerkReady(timeoutMs = 5000): Promise<boolean> {
  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) return false;
  if (_isClerkReady) return true;

  await Promise.race([
    _clerkReady.then(() => {
      _isClerkReady = true;
    }),
    new Promise<void>((resolve) => setTimeout(resolve, timeoutMs)),
  ]);

  return _isClerkReady;
}

export function isAuthConfigured(): boolean {
  return !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
}

async function requireAuthToken(timeoutMs?: number): Promise<string | null> {
  if (!isAuthConfigured()) return null;

  const ready = await waitForClerkReady(timeoutMs ?? 5000);
  if (!ready) {
    throw new Error("Authentication is still loading. Please try again.");
  }

  const token = await getAuthToken();
  if (!token) {
    throw new Error("Authentication token is not available. Please sign in again.");
  }

  return token;
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const payload = token.split(".")[1];
    if (!payload) return null;
    const padded = payload.replace(/-/g, "+").replace(/_/g, "/").padEnd(
      Math.ceil(payload.length / 4) * 4,
      "=",
    );
    return JSON.parse(globalThis.atob(padded)) as Record<string, unknown>;
  } catch {
    return null;
  }
}

export async function getClientCacheScope(options?: {
  timeoutMs?: number;
}): Promise<string | null> {
  if (!isAuthConfigured()) return "local";
  const token = await getAuthToken({
    waitForClerk: true,
    timeoutMs: options?.timeoutMs ?? 5000,
  });
  if (!token) return null;
  const sub = decodeJwtPayload(token)?.sub;
  return typeof sub === "string" && sub ? `user:${sub}` : `token:${token.slice(0, 24)}`;
}

/** Returns the current Clerk JWT, or null if auth is not configured. */
export async function getAuthToken(options?: {
  waitForClerk?: boolean;
  timeoutMs?: number;
}): Promise<string | null> {
  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) return null;
  if (options?.waitForClerk) {
    await waitForClerkReady(options.timeoutMs);
  }
  return _getToken ? _getToken() : null;
}

/* ── helpers ──────────────────────────────────────────────── */

async function fetchWithAuth(
  url: string,
  options: RequestInit & { timeoutMs?: number } = {},
  token?: string | null,
): Promise<Response> {
  const { timeoutMs, signal, ...requestInit } = options;
  const controller = timeoutMs ? new AbortController() : null;
  const timeoutId = controller
    ? window.setTimeout(() => controller.abort(new Error("Request timed out")), timeoutMs)
    : null;

  if (controller && signal) {
    if (signal.aborted) {
      controller.abort(signal.reason);
    } else {
      signal.addEventListener(
        "abort",
        () => controller.abort(signal.reason),
        { once: true },
      );
    }
  }

  try {
    return await fetch(`${BASE}${url}`, {
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(requestInit.headers as Record<string, string>),
      },
      ...requestInit,
      signal: controller?.signal ?? signal,
    });
  } finally {
    if (timeoutId !== null) {
      window.clearTimeout(timeoutId);
    }
  }
}

async function request(
  url: string,
  options: RequestInit & { timeoutMs?: number } = {},
): Promise<Response> {
  let token = await requireAuthToken(options.timeoutMs);
  let res = await fetchWithAuth(url, options, token);

  if (res.status === 401 && process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) {
    const isReady = await waitForClerkReady();
    if (isReady) {
      const retryToken = await getAuthToken();
      if (retryToken && retryToken !== token) {
        token = retryToken;
        res = await fetchWithAuth(url, options, token);
      }
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res;
}

/* ── Settings ─────────────────────────────────────────────── */

export async function getSettings(options?: {
  timeoutMs?: number;
  signal?: AbortSignal;
}): Promise<Settings> {
  const res = await request("/settings", {
    timeoutMs: options?.timeoutMs,
    signal: options?.signal,
  });
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
  const res = await request("/papers/export", {
    method: "POST",
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
