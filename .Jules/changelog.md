# Jules Changelog

## 2026-01-01 - v0.1.0

### Added
- **Toast Notification System:** Created a robust toast notification system with `ToastContext` and `ToastContainer`.
- **UI Component:** Added `web/components/ui/Toast.tsx` with support for both Neobrutalism and Glassmorphism themes.

### Changed
- **UX Improvement:** Replaced native `alert()` calls in `GroupDetails.tsx` with non-blocking toast notifications for better user experience.
- **App Structure:** Wrapped the web application with `ToastProvider` in `App.tsx`.

**Files Modified:**
- `web/contexts/ToastContext.tsx`
- `web/components/ui/Toast.tsx`
- `web/App.tsx`
- `web/pages/GroupDetails.tsx`
