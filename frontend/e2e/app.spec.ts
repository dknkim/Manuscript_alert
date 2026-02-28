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
    await expect(page.locator("h1")).toContainText("Manuscript Alert System");
  });

  test("shows 3 tab buttons", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("button", { name: "📚Papers" })).toBeVisible();
    await expect(page.getByRole("button", { name: "🤖Models" })).toBeVisible();
    await expect(page.getByRole("button", { name: "⚙️Settings" })).toBeVisible();
  });

  test("Papers tab is active by default", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Recent Papers" })).toBeVisible();
    await expect(page.getByRole("heading", { name: /Configuration/ })).toBeVisible();
  });
});

test.describe("Tab navigation", () => {
  test("switches to Models tab", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "🤖Models" }).click();
    await expect(page.getByText("Model Management")).toBeVisible();
  });

  test("switches to Settings tab", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "⚙️Settings" }).click();
    await expect(page.getByText("Application Settings")).toBeVisible();
  });

  test("switches back to Papers tab", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "⚙️Settings" }).click();
    await page.getByRole("button", { name: "📚Papers" }).click();
    await expect(page.getByRole("heading", { name: "Recent Papers" })).toBeVisible();
  });
});

test.describe("Papers tab", () => {
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
    await expect(page.getByRole("button", { name: /Fetch Papers/ })).toBeVisible();
  });

  test("shows keywords preview", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText(/Active Keywords/)).toBeVisible();
  });
});

test.describe("Settings tab", () => {
  test("shows 4 sub-tabs", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "⚙️Settings" }).click();
    await expect(page.getByRole("button", { name: "🔍 Keywords" })).toBeVisible();
    await expect(page.getByRole("button", { name: "📰 Journals" })).toBeVisible();
    await expect(page.getByRole("button", { name: "📊 Scoring" })).toBeVisible();
    await expect(page.getByRole("button", { name: "💾 Backup" })).toBeVisible();
  });

  test("switches between settings sub-tabs", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "⚙️Settings" }).click();

    // Default: Keywords
    await expect(page.getByText("Research Keywords")).toBeVisible();

    // Switch to Journals
    await page.getByRole("button", { name: "📰 Journals" }).click();
    await expect(page.getByText("Target Journals")).toBeVisible();

    // Switch to Scoring
    await page.getByRole("button", { name: "📊 Scoring" }).click();
    await expect(page.getByRole("heading", { name: "Journal Impact Scoring" })).toBeVisible();

    // Switch to Backup
    await page.getByRole("button", { name: "💾 Backup" }).click();
    await expect(page.getByText("Available Backups")).toBeVisible();
  });
});

test.describe("Models tab", () => {
  test("shows model management UI", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "🤖Models" }).click();
    await expect(page.getByText("Model Management")).toBeVisible();
    await expect(page.getByText("Save Current Settings as Model")).toBeVisible();
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

  test("settings tab layout", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "⚙️Settings" }).click();
    await expect(page.getByText("Research Keywords")).toBeVisible();
    await expect(page).toHaveScreenshot("settings-tab.png", {
      maxDiffPixelRatio: 0.02,
    });
  });

  test("models tab layout", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "🤖Models" }).click();
    await expect(page.getByText("Model Management")).toBeVisible();
    await expect(page).toHaveScreenshot("models-tab.png", {
      maxDiffPixelRatio: 0.02,
    });
  });
});
