# Splitwiser UI/UX Changelog

> All UI/UX changes made by Jules automated enhancement agent.

---

## [Unreleased]

### Added
- Dashboard skeleton loading state (`DashboardSkeleton`) to improve perceived performance during data fetch.
- Comprehensive `EmptyState` component for Groups and Friends pages to better guide new users.
- Global Toast notification system (`ToastContext` + `ToastContainer`) supporting both Glassmorphism and Neobrutalism themes.
- Integrated toast notifications in `Auth.tsx` for login/signup errors and `GroupDetails.tsx` for expense/group actions.

### Changed
- Replaced native `alert()` calls in `GroupDetails.tsx` with toast notifications for a smoother UX.
- Improved error handling in `Auth.tsx` to display backend error messages in toasts.

### Planned
- See `todo.md` for queued tasks

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

---
