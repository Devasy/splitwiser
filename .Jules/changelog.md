# Splitwiser UI/UX Changelog

> All UI/UX changes made by Jules automated enhancement agent.

---

## [Unreleased]

### Added
- **Mobile Skeleton Loading:** Implemented a reusable skeleton loading system for the mobile app.
  - **Features:**
    - Created `Skeleton` component with pulsing animation using `Animated` and `useTheme`.
    - Created `GroupListSkeleton` component mimicking the layout of group cards.
    - Integrated skeleton loading into `HomeScreen`, replacing the generic spinner.
  - **Technical:** Created `mobile/components/ui/Skeleton.js` and `mobile/components/skeletons/GroupListSkeleton.js`. Updated `mobile/screens/HomeScreen.js`.

- **Password Strength Meter:** Added a visual password strength indicator to the signup form.
  - **Features:**
    - Real-time strength calculation (Length, Uppercase, Lowercase, Number, Symbol).
    - Visual feedback with segmented progress bar and color coding.
    - Specific criteria checklist (6+ chars, Mixed case, Number, Symbol).
    - Dual-theme support (Neobrutalism & Glassmorphism).
    - Accessible ARIA live region for screen readers.
  - **Technical:** Created `web/components/ui/PasswordStrength.tsx`. Integrated into `web/pages/Auth.tsx`.

- **Mobile Haptics:** Implemented system-wide haptic feedback for all interactive elements.
  - **Features:**
    - Created `HapticButton`, `HapticIconButton`, `HapticFAB`, `HapticCard`, `HapticList`, `HapticCheckbox`, `HapticMenu`, `HapticSegmentedButtons`, `HapticAppbar` (including `HapticAppbarAction`, `HapticAppbarBackAction`) wrappers.
    - Integrated into all screens (`Home`, `GroupDetails`, `AddExpense`, `Friends`, `Account`, `EditProfile`, `Login`, `Signup`, `JoinGroup`, `GroupSettings`, `SplitwiseImport`).
    - Uses `expo-haptics` with `Light` impact style for subtle feedback.
  - **Technical:** Centralized haptic logic in `mobile/components/ui/` to ensure consistency and maintainability.

- **Mobile Accessibility:** Completed accessibility audit for all mobile screens.
  - **Features:**
    - Added `accessibilityLabel` to all interactive elements (buttons, inputs, list items).
    - Added `accessibilityRole` to ensure screen readers identify element types correctly.
    - Added `accessibilityHint` for clearer context on destructive actions or complex interactions.
    - Covered Auth, Dashboard, Groups, and Utility screens.
  - **Technical:** Updated all files in `mobile/screens/` to compliant with React Native accessibility standards.

- **Mobile Pull-to-Refresh:** Implemented native pull-to-refresh interactions with haptic feedback for key lists.
  - **Features:**
    - Integrated `RefreshControl` into `HomeScreen`, `FriendsScreen`, and `GroupDetailsScreen`.
    - Added haptic feedback (`Haptics.ImpactFeedbackStyle.Light`) on refresh trigger.
    - Separated 'isRefreshing' state from 'isLoading' to prevent full-screen spinner interruptions.
    - Themed the refresh spinner using `react-native-paper`'s primary color.
  - **Technical:** Installed `expo-haptics`. Refactored data fetching logic to support silent updates.

- **Confirmation Dialog System:** Replaced browser's native `alert`/`confirm` with a custom, accessible, and themed modal system.
  - **Features:**
    - Dual-theme support (Glassmorphism & Neobrutalism).
    - Asynchronous `useConfirm` hook returning a Promise.
    - Specialized variants (danger, warning, info) with appropriate styling and icons.
    - Fully accessible `Modal` component (added `role="dialog"`, `aria-labelledby`, `aria-modal`).
  - **Technical:** Created `web/components/ui/ConfirmDialog.tsx`, `web/contexts/ConfirmContext.tsx`. Updated `web/pages/GroupDetails.tsx` to use the new system.

- **Error Boundary System:** Implemented a global React Error Boundary to catch render errors gracefully.
  - **Features:**
    - Dual-theme support (Glassmorphism & Neobrutalism) for the error fallback UI.
    - "Retry" button to reset error state and re-render.
    - "Home" button to navigate back to safety.
    - Captures errors in `AppRoutes` and displays a user-friendly message instead of a white screen.
  - **Technical:** Created `web/components/ErrorBoundary.tsx` using a hybrid Class+Functional approach to support Hooks in the fallback UI. Integrated into `web/App.tsx`.

- Inline form validation in Auth page with real-time feedback and proper ARIA accessibility support (`aria-invalid`, `aria-describedby`, `role="alert"`).
- Dashboard skeleton loading state (`DashboardSkeleton`) to improve perceived performance during data fetch.
- Comprehensive `EmptyState` component for Groups and Friends pages to better guide new users.
- Toast notification system (`ToastContext`, `Toast` component) for providing non-blocking user feedback.
- Keyboard navigation support for Groups page, enabling accessibility for power users.

### Changed
- **Web App:** Refactored `GroupDetails` destructive actions (Delete Group, Delete Expense, Leave Group, Remove Member) to use the new `ConfirmDialog` instead of `window.confirm`.
- **Accessibility:** Updated `Modal` component to include proper ARIA roles and labels, fixing a long-standing accessibility gap.
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
