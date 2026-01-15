# Splitwiser UI/UX Changelog

> All UI/UX changes made by Jules automated enhancement agent.

---

## [Unreleased]

### Added
- **Error Boundary:** Added a global `ErrorBoundary` component that catches unexpected errors and displays a friendly, dual-themed fallback UI with a retry action.
- Inline form validation in Auth page with real-time feedback and proper ARIA accessibility support (`aria-invalid`, `aria-describedby`, `role="alert"`).
- Dashboard skeleton loading state (`DashboardSkeleton`) to improve perceived performance during data fetch.
- Comprehensive `EmptyState` component for Groups and Friends pages to better guide new users.
- Toast notification system (`ToastContext`, `Toast` component) for providing non-blocking user feedback.
- Keyboard navigation support for Groups page, enabling accessibility for power users.

### Changed
- Updated JULES_PROMPT.md based on review of successful PRs:
  - Emphasized complete system implementation over piecemeal changes
  - Added best practices from successful PRs (Toast system, keyboard navigation iteration)
  - Refined task categories to focus on complete features
  - Enhanced validation checklist
  - Added implementation phases guide
  - Documented successful patterns to repeat

### Planned
- See `todo.md` for queued tasks

---

## [2026-01-13] - Prompt Optimization

### Changed
- **Streamlined JULES_PROMPT.md** (336 → 179 lines, 47% reduction):
  - Removed completed task lists (moved to changelog/knowledge)
  - Removed redundant "best practices" examples
  - Consolidated duplicate sections
  - Kept only actionable guidance
- **Reviewed merged PRs** (#227, #236, #234, #226, #225)
- **Updated knowledge.md** with detailed PR reviews and successful patterns

**Key Insights:**
1. Complete systems > piecemeal changes
2. Accessibility and theme support from the start
3. Semantic HTML over manual ARIA when possible
4. Multiple commits in PRs were often from review feedback, not agent iteration

**Files Modified:**
- `.jules/JULES_PROMPT.md` (streamlined and optimized)
- `.jules/knowledge.md` (added PR review section)
- `.jules/changelog.md`

---

## [2026-01-01] - Initial Setup

### Added
- Created Jules agent documentation and tracking system
- `.Jules/JULES_PROMPT.md` - Main agent instructions
- `.Jules/todo.md` - Task queue with prioritized improvements
- `.Jules/knowledge.md` - Codebase knowledge base
- `.Jules/changelog.md` - This changelog

### Analysis Completed
- Full audit of `web/` application structure
- Full audit of `mobile/` application structure
- Identified accessibility gaps
- Identified UX improvement opportunities
- Documented theming system patterns
- Documented component APIs

**Files Created:**
- `.jules/JULES_PROMPT.md`
- `.jules/todo.md`
- `.jules/knowledge.md`
- `.jules/changelog.md`
