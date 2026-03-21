# High Impact → Relevant: Internal Variable Rename Scope

## Context
UI strings already use "Relevant Journals" / "Relevant" consistently. Only internal variable names still say "high impact". This doc tracks the full rename scope for when we tackle it.

## Frontend (14 files — all under `frontend/`)

| File | Variables/Fields |
|---|---|
| `frontend/src/types/index.ts` | `is_high_impact` field on Paper type |
| `frontend/src/hooks/usePaperSearch.ts` | `highImpactOnly` state, `setHighImpactOnly` |
| `frontend/src/app/page.tsx` | `search.highImpactOnly` references |
| `frontend/src/components/Statistics.tsx` | `highImpact` local var, `highImpactOnly` / `onHighImpactChange` props |
| `frontend/src/components/features/DashboardPanel.tsx` | `highImpactOnly` / `onHighImpactChange` prop threading |
| `frontend/src/components/features/SearchPanel.tsx` | `highImpactOnly` prop + checkbox handler |
| `frontend/src/components/PapersTab.tsx` | legacy component references |
| `frontend/src/components/PaperCard.tsx` | `is_high_impact` badge logic |
| `frontend/src/components/SettingsTab.tsx` | journals reference |
| `frontend/src/__tests__/Statistics.test.tsx` | test props |
| `frontend/src/__tests__/fixtures.ts` | mock data `is_high_impact` |
| `frontend/src/__tests__/api.test.ts` | mock data |
| `frontend/src/__tests__/PaperCard.test.tsx` | test assertions |
| `frontend/src/__tests__/README.md` | docs mention |

## Backend (5 real files + backups — all under `backend/`)

| File | Variables/Fields |
|---|---|
| `backend/config/settings.py` | `high_impact_journals` list |
| `backend/src/utils/constants.py` | journal matching constants |
| `backend/src/utils/journal_utils.py` | journal matching logic |
| `backend/src/services/paper_service.py` | sets `is_high_impact` on papers |
| `backend/src/services/settings_service.py` | settings handling |

## Data (breaking change — requires migration)
- `backend/data/archive/archive.json` — stored papers with `is_high_impact` field
- `backend/config/models/*.json` — model configs with `is_high_impact` field

## Notes
- Renaming `is_high_impact` in API response is a breaking change across frontend + backend
- Archive JSON and model JSONs need data migration
- Consider doing frontend-only rename first (map `is_high_impact` → `isRelevantJournal` at the API boundary)
