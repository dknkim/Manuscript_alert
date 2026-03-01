# UX Improvements — Manuscript Alert (Next.js)

Last updated: 2026-02-28

## Status

| ID | Proposal | Effort | Status |
|----|----------|--------|--------|
| P2-D | Fix PaperDetailDrawer dark mode tokens | Trivial | Done |
| P1-B | Move Fetch button to top of SearchPanel | Trivial | Done |
| P1-C | Reorder sidebar controls by change frequency | Trivial | Done |
| P1-D | Swap Stats/Detail in DashboardPanel (not stack) | Trivial | Done |
| P3-E | Keyboard accessibility (card focus, labels, touch targets) | Low | Done |
| P1-A | Skeleton loading cards instead of spinner | Low | Done |
| Score | Redesign score display to be meaningful | Low | Done |
| Score-2 | Normalize scoring to 0-10 (BM25 saturation + exponential norm) | Medium | Done |
| P2-A | Score as colored left-border on cards | Low | Done |
| P4-A | Selected card ring state | Trivial | Done |
| P1-E | Always render 3-column layout (no post-fetch shift) | Low | Done |

## Backlog (not started)

| ID | Proposal | Effort | Impact |
|----|----------|--------|--------|
| P2-B | Card info restructure (date first, keywords before abstract) | Low | Medium |
| P2-C | Contextual empty states (Lucide icons, actionable text) | Low | Medium |
| P3-A | Keyword pills with match counts post-fetch | Medium | High |
| P3-B | Sticky "last fetched" timestamp | Low | Medium |
| P3-C | Center-align nav, aria-current, fix disabled KB element | Low | Medium |
| P3-D | Sort controls (Relevance / Newest / Journal) | Medium | High |
| P4-B | Elapsed fetch timer | Low | Low |
| P4-C | Statistics source bars + fix display names | Low | Low |

## Detail

### P2-D: Fix PaperDetailDrawer dark mode tokens
`PaperDetailDrawer.tsx` uses hardcoded `bg-white`, `text-gray-*`, `bg-indigo-*` instead of design tokens. Completely broken in dark mode.

Token mapping: `bg-white` -> `bg-surface-raised`, `text-gray-900` -> `text-text-primary`, `text-gray-600/700` -> `text-text-secondary`, `bg-indigo-50 text-indigo-700` -> `bg-accent-subtle text-accent-text`, `text-indigo-600` -> `text-accent`.

### P1-B + P1-C: Reorder SearchPanel
New order: Mode toggle > **Fetch button** > Data Sources > Search Limits > Journal Quality > Active Keywords. Moves primary action up, orders controls by change frequency.

### P1-D: Swap Stats/Detail in DashboardPanel
Currently Statistics and PaperDetailDrawer stack vertically (user has to scroll). Change to: show one OR the other. Paper selected -> show detail. Close detail -> show stats.

### P3-E: Keyboard accessibility
- PaperCard wrapper `<div onClick>` needs `role="button" tabIndex={0} onKeyDown`
- Search input in PaperFeed needs `<label className="sr-only">`
- Archive button needs `min-h-[44px]` touch target (WCAG 2.5.5)
- ScoreIndicator needs `aria-label`

### P1-A: Skeleton loading cards
Replace single centered spinner with 5-6 skeleton card shapes matching PaperCard layout. Use `animate-pulse` shimmer. Show per-source status line above skeletons.

### Score redesign
Added color-coded display with green (7.5+) / amber (5+) / orange (2.5+) / red (<2.5) tiers. Shows "X.X / 10" format with colored left-border accent on cards.

### Score-2: BM25-inspired scoring + normalization
Replaced the raw keyword-match accumulation with a proper scoring pipeline:
- **BM25 saturation** for term frequency: `tf*(k1+1)/(tf+k1)` with k1=1.5 — repeated keyword occurrences give diminishing returns instead of linear bonus
- **Removed title×3 hack** — title matches now use explicit weighted bonus (0.5×) instead of inflating the match count
- **Removed hardcoded keyword bonus** for "pet"/"mri" — priority system handles domain-specific weighting
- **Exponential saturation normalization** to 0-10: `10*(1-e^(-raw/k))` where k scales with keyword count — naturally bounds scores, handles outliers (journal boosts) gracefully, and produces absolute scores (not batch-relative)
