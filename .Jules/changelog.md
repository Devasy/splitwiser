# Splitwiser UI/UX Changelog

> All UI/UX changes made by Jules automated enhancement agent.

---

## [Unreleased]

### Added
- Global `ErrorBoundary` component to catch and display unhandled errors gracefully.
- Support for dual themes (Neobrutalism/Glassmorphism) in `ErrorBoundary` fallback UI.
- Retry functionality in `ErrorBoundary` to allow users to recover from crashes without refreshing.

### Changed
- Wrapped `AppRoutes` and `ToastContainer` with `ErrorBoundary` in `web/App.tsx`.
- Installed `@types/react` and `@types/react-dom` to fix TypeScript issues with class components.

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
