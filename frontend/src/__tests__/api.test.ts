import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  getSettings,
  saveSettings,
  fetchPapers,
  listModels,
  saveModel,
  loadModel,
  deleteModel,
  listBackups,
  archivePaper,
  getArchivedPapers,
  unarchivePaper,
} from "@/lib/api";
import { mockSettings, mockPaperHighImpact } from "./fixtures";

// Mock global fetch
const mockFetch = vi.fn();
globalThis.fetch = mockFetch;

function jsonResponse(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? "OK" : "Error",
    json: () => Promise.resolve(data),
    blob: () => Promise.resolve(new Blob()),
  } as Response);
}

describe("API client", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("getSettings calls GET /settings", async () => {
    mockFetch.mockReturnValue(jsonResponse(mockSettings));
    const result = await getSettings();
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/settings",
      expect.objectContaining({ headers: expect.any(Object) }),
    );
    expect(result.keywords).toEqual(mockSettings.keywords);
  });

  it("saveSettings calls PUT /settings", async () => {
    mockFetch.mockReturnValue(jsonResponse({ status: "ok" }));
    const result = await saveSettings(mockSettings);
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/settings",
      expect.objectContaining({ method: "PUT" }),
    );
    expect(result.status).toBe("ok");
  });

  it("fetchPapers calls POST /papers/fetch", async () => {
    mockFetch.mockReturnValue(
      jsonResponse({ papers: [], total_before_filter: 0, total_after_filter: 0, errors: [], must_have_keywords: [] }),
    );
    const sources = { pubmed: true, arxiv: false, biorxiv: false, medrxiv: false };
    await fetchPapers(sources, "Brief");
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/papers/fetch",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("listModels calls GET /models", async () => {
    mockFetch.mockReturnValue(jsonResponse([]));
    await listModels();
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/models",
      expect.objectContaining({ headers: expect.any(Object) }),
    );
  });

  it("saveModel calls POST /models", async () => {
    mockFetch.mockReturnValue(jsonResponse({ status: "ok", filename: "Test.json" }));
    await saveModel("Test");
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/models",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("loadModel calls POST /models/{filename}/load", async () => {
    mockFetch.mockReturnValue(jsonResponse({ status: "ok" }));
    await loadModel("Test.json");
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/models/Test.json/load",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("deleteModel calls DELETE /models/{filename}", async () => {
    mockFetch.mockReturnValue(jsonResponse({ status: "ok" }));
    await deleteModel("Test.json");
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/models/Test.json",
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  it("listBackups calls GET /backups", async () => {
    mockFetch.mockReturnValue(jsonResponse([]));
    await listBackups();
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/backups",
      expect.objectContaining({ headers: expect.any(Object) }),
    );
  });

  it("archivePaper calls POST /papers/archive", async () => {
    mockFetch.mockReturnValue(jsonResponse({ status: "ok" }));
    await archivePaper(mockPaperHighImpact);
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/papers/archive",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("getArchivedPapers calls GET /papers/archive", async () => {
    mockFetch.mockReturnValue(jsonResponse({ archive: {}, archived_titles: [], total: 0 }));
    await getArchivedPapers();
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/papers/archive",
      expect.objectContaining({ headers: expect.any(Object) }),
    );
  });

  it("unarchivePaper calls DELETE /papers/archive", async () => {
    mockFetch.mockReturnValue(jsonResponse({ status: "ok" }));
    await unarchivePaper("Test Paper", "2026-02-27");
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/papers/archive",
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  it("throws on non-ok response with error detail", async () => {
    mockFetch.mockReturnValue(
      jsonResponse({ detail: "Not found" }, 404),
    );
    await expect(getSettings()).rejects.toThrow("Not found");
  });

  it("throws on non-ok response with fallback message", async () => {
    mockFetch.mockReturnValue(
      Promise.resolve({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
        json: () => Promise.reject(new Error("parse error")),
      } as Response),
    );
    await expect(getSettings()).rejects.toThrow("Internal Server Error");
  });
});
