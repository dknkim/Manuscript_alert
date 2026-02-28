# E2E Tests

End-to-end tests using [Playwright](https://playwright.dev/). Requires the full stack running.

## Running tests

```bash
# Start the server first
python server.py

# Run all E2E tests (in another terminal)
PLAYWRIGHT_BASE_URL=http://localhost:8000 npm run test:e2e

# Interactive UI mode
PLAYWRIGHT_BASE_URL=http://localhost:8000 npm run test:e2e:ui

# Update visual regression baselines
PLAYWRIGHT_BASE_URL=http://localhost:8000 npx playwright test --update-snapshots
```

## Structure

```
e2e/
├── app.spec.ts           # All E2E tests (13 functional + 3 visual regression)
└── app.spec.ts-snapshots/ # Visual regression baseline screenshots
    ├── homepage-chromium-darwin.png
    ├── settings-tab-chromium-darwin.png
    └── models-tab-chromium-darwin.png
```

## Visual regression

Playwright's built-in `toHaveScreenshot()` compares screenshots pixel-by-pixel against stored baselines. The `maxDiffPixelRatio: 0.02` threshold allows up to 2% pixel difference.

Baselines are **platform-specific** — filenames include the OS (e.g., `darwin`, `linux`). Visual regression tests are **opt-in** — skipped by default, run with:

```bash
VR=1 PLAYWRIGHT_BASE_URL=http://localhost:8000 npm run test:e2e
```

To regenerate baselines after intentional UI changes:

```bash
VR=1 PLAYWRIGHT_BASE_URL=http://localhost:8000 npx playwright test --update-snapshots --grep "Visual regression"
```

## Configuration

`playwright.config.ts` (in `frontend/`) configures:
- Browser: Chromium only
- Base URL: `http://localhost:8000` (via `PLAYWRIGHT_BASE_URL` env var)
- Retries: 0 locally, 2 in CI
- Screenshots on failure: captured automatically
