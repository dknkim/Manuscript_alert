# Frontend Tests

Component tests using [Vitest](https://vitest.dev/) + [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/).

## Running tests

```bash
# All component tests
npm test

# Watch mode (re-runs on file changes)
npm run test:watch

# Single file
npx vitest run src/__tests__/PaperCard.test.tsx

# Single test by name
npx vitest run -t "shows loading spinner"
```

## Structure

```
src/__tests__/
├── setup.ts              # Test environment setup (jest-dom matchers)
├── fixtures.ts           # Shared mock data (settings, papers, models, backups)
├── api.test.ts           # API client unit tests (mocks global fetch)
├── PaperCard.test.tsx    # PaperCard component (18 tests)
├── Statistics.test.tsx   # Statistics sidebar (9 tests)
├── PapersTab.test.tsx    # Papers tab container (19 tests)
├── ModelsTab.test.tsx    # Models tab (10 tests)
└── SettingsTab.test.tsx  # Settings tab with sub-tabs (15 tests)
```

## Key files

- **`setup.ts`** — Imports `@testing-library/jest-dom/vitest` for DOM matchers like `toBeInTheDocument()`.
- **`fixtures.ts`** — Shared test data used across all test files. Contains `mockSettings`, `mockFetchResult`, `mockPaperHighImpact`, `mockModels`, etc.
- **`vitest.config.ts`** (in `frontend/`) — Vitest config with React plugin, jsdom environment, and `@/` path alias.

## Conventions

- Tests use React Testing Library queries (`getByRole`, `getByText`, `getByLabelText`) to test user-visible behavior, not implementation details.
- API modules are mocked with `vi.mock("@/lib/api")` so component tests don't make real network calls.
- When buttons share partial text (e.g., "Keywords" tab vs "Save Keywords" button), use exact names or emoji prefixes to disambiguate selectors.

## Related: E2E & Visual Regression

E2E and visual regression tests live in `frontend/e2e/` — see `e2e/README.md`. Visual regression is opt-in only: `VR=1 npm run test:e2e`.
