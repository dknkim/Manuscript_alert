const BASE = "/api";

async function request(url, options = {}) {
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

// ---------- Settings ----------
export async function getSettings() {
  const res = await request("/settings");
  return res.json();
}

export async function saveSettings(settings) {
  const res = await request("/settings", {
    method: "PUT",
    body: JSON.stringify({ settings }),
  });
  return res.json();
}

// ---------- Papers ----------
export async function fetchPapers(dataSources, searchMode) {
  const res = await request("/papers/fetch", {
    method: "POST",
    body: JSON.stringify({ data_sources: dataSources, search_mode: searchMode }),
  });
  return res.json();
}

export async function exportPapersCSV(dataSources, searchMode) {
  const res = await fetch(`${BASE}/papers/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ data_sources: dataSources, search_mode: searchMode }),
  });
  return res.blob();
}

// ---------- Models ----------
export async function listModels() {
  const res = await request("/models");
  return res.json();
}

export async function saveModel(name) {
  const res = await request("/models", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  return res.json();
}

export async function loadModel(filename) {
  const res = await request(`/models/${filename}/load`, { method: "POST" });
  return res.json();
}

export async function previewModel(filename) {
  const res = await request(`/models/${filename}/preview`);
  return res.json();
}

export async function deleteModel(filename) {
  const res = await request(`/models/${filename}`, { method: "DELETE" });
  return res.json();
}

// ---------- Backups ----------
export async function listBackups() {
  const res = await request("/backups");
  return res.json();
}

export async function restoreBackup(path) {
  const res = await request("/backups/restore", {
    method: "POST",
    body: JSON.stringify({ path }),
  });
  return res.json();
}

export async function createBackup() {
  const res = await request("/backups/create", { method: "POST" });
  return res.json();
}
