import { test, expect } from "@playwright/test";

/**
 * E2E tests for the Manuscript Alert frontend.
 *
 * These require the full stack running:
 *   python server.py  (serves both API + frontend on :8000)
 *
 * Run with: npm run test:e2e
 */

test.describe("App loading", () => {
  test("loads homepage and shows title", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("h1")).toContainText("Manuscript Alert");
  });

  test("shows navigation links", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("link", { name: "Papers" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Models" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Settings" })).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Knowledge Base" }),
    ).toBeVisible();
  });

  test("Papers page is shown by default", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: "Recent Papers" }),
    ).toBeVisible();
  });
});

test.describe("Route navigation", () => {
  test("navigates to Models page", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "Models" }).click();
    await expect(page.getByText("Model Management")).toBeVisible();
  });

  test("navigates to Settings page", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "Settings" }).click();
    await expect(page.getByText("Application Settings")).toBeVisible();
  });

  test("navigates back to Papers page", async ({ page }) => {
    await page.goto("/settings");
    await page.getByRole("link", { name: "Papers" }).click();
    await expect(
      page.getByRole("heading", { name: "Recent Papers" }),
    ).toBeVisible();
  });
});

test.describe("Papers page", () => {
  test("shows data source checkboxes", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByLabel("arXiv")).toBeVisible();
    await expect(page.getByLabel("bioRxiv")).toBeVisible();
    await expect(page.getByLabel("medRxiv")).toBeVisible();
    await expect(page.getByLabel("PubMed")).toBeVisible();
  });

  test("shows search mode radio buttons", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByLabel(/Brief/)).toBeVisible();
    await expect(page.getByLabel(/Standard/)).toBeVisible();
    await expect(page.getByLabel(/Extended/)).toBeVisible();
  });

  test("shows fetch button", async ({ page }) => {
    await page.goto("/");
    // Button may show "Fetching…" during auto-fetch or "Fetch Papers" after
    await expect(
      page.getByRole("button", { name: /Fetch/ }),
    ).toBeVisible();
  });

  test("shows keywords preview", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText(/Active Keywords/)).toBeVisible();
  });
});

test.describe("Settings page", () => {
  test("shows 4 sub-tabs", async ({ page }) => {
    await page.goto("/settings");
    await expect(
      page.getByRole("button", { name: "🔍 Keywords" }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "📰 Journals" }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "📊 Scoring" }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "💾 Backup" }),
    ).toBeVisible();
  });

  test("switches between settings sub-tabs", async ({ page }) => {
    await page.goto("/settings");

    // Default: Keywords
    await expect(page.getByText("Research Keywords")).toBeVisible();

    // Switch to Journals
    await page.getByRole("button", { name: /Journals/ }).click();
    await expect(page.getByText("Target Journals")).toBeVisible();

    // Switch to Scoring
    await page.getByRole("button", { name: /Scoring/ }).click();
    await expect(
      page.getByRole("heading", { name: "Journal Impact Scoring" }),
    ).toBeVisible();

    // Switch to Backup
    await page.getByRole("button", { name: /Backup/ }).click();
    await expect(page.getByText("Available Backups")).toBeVisible();
  });
});

test.describe("Models page", () => {
  test("shows model management UI", async ({ page }) => {
    await page.goto("/models");
    await expect(page.getByText("Model Management")).toBeVisible();
    await expect(
      page.getByText("Save Current Settings as Model"),
    ).toBeVisible();
    await expect(page.getByText("Quick Actions")).toBeVisible();
  });
});

// Visual regression screenshots are platform-specific (darwin vs linux).
// Opt-in only: run with VR=1 npm run test:e2e
test.describe("Visual regression", () => {
  test.skip(!process.env.VR, "Set VR=1 to run visual regression tests");

  test("homepage layout", async ({ page }) => {
    await page.goto("/");
    // Wait for settings to load (spinner disappears)
    await page.waitForSelector("h1");
    await expect(page).toHaveScreenshot("homepage.png", {
      maxDiffPixelRatio: 0.02,
    });
  });

  test("settings page layout", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.getByText("Research Keywords")).toBeVisible();
    await expect(page).toHaveScreenshot("settings-tab.png", {
      maxDiffPixelRatio: 0.02,
    });
  });

  test("models page layout", async ({ page }) => {
    await page.goto("/models");
    await expect(page.getByText("Model Management")).toBeVisible();
    await expect(page).toHaveScreenshot("models-tab.png", {
      maxDiffPixelRatio: 0.02,
    });
  });
});
