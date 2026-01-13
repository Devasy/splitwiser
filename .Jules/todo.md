# Jules TODO List

> Meaningful, user-noticeable improvements for Splitwiser. Each task should take 30-100 lines and have clear impact.

**Note:** After previous agent mistakes, tasks are now grouped into meaningful units that users will actually notice.

---

## 🔴 High Priority (User-Facing Impact)

### Web

- [x] **[ux]** Complete skeleton loading system for Dashboard
  - Completed: 2026-01-01
  - Files modified: `web/pages/Dashboard.tsx`, `web/components/skeletons/DashboardSkeleton.tsx`
  - Impact: Professional loading experience that mimics actual content layout

- [x] **[ux]** Toast notification system for user actions
  - Completed: 2026-01-01
  - Files modified: `web/contexts/ToastContext.tsx`, `web/components/ui/Toast.tsx`, `web/App.tsx`, `web/pages/Auth.tsx`
  - Impact: Modern feedback system that supports both themes

- [x] **[a11y]** Complete keyboard navigation for Groups page
  - Completed: 2026-01-01
  - File: `web/pages/Groups.tsx`
  - Context: Add keyboard handling to group cards + search + modals
  - Impact: Full keyboard accessibility for power users
  - Size: ~50 lines

- [x] **[ux]** Comprehensive empty states with illustrations
  - Completed: 2026-01-01
  - Files: `web/pages/Groups.tsx`, `web/pages/Friends.tsx`
  - Context: Create illustrated empty states with CTAs (not just text)
  - Impact: Guides new users, makes app feel polished
  - Size: ~70 lines

- [x] **[ux]** Error boundary with retry for API failures
  - Files: Create `web/components/ErrorBoundary.tsx`, wrap app
  - Context: Catch errors gracefully with retry button
  - Impact: App doesn't crash, users can recover
  - Size: ~60 lines
  - Completed: 2026-01-14

### Mobile

- [ ] **[ux]** Pull-to-refresh with haptic feedback on all list screens
  - Files: `mobile/screens/HomeScreen.js`, `mobile/screens/GroupDetailsScreen.js`
  - Context: Add RefreshControl + Expo Haptics to main lists
  - Impact: Native feel, users can easily refresh data
  - Size: ~45 lines
  - Added: 2026-01-01

- [ ] **[ux]** Complete skeleton loading for HomeScreen groups
  - File: `mobile/screens/HomeScreen.js`
  - Context: Replace ActivityIndicator with skeleton group cards
  - Impact: Better loading experience, less jarring
  - Size: ~40 lines
  - Added: 2026-01-01

- [ ] **[a11y]** Complete accessibility labels for all screens
  - Files: All screens in `mobile/screens/`
  - Context: Add accessibilityLabel, accessibilityHint, accessibilityRole throughout
  - Impact: Screen reader users can use app fully
  - Size: ~60 lines across files
  - Added: 2026-01-01

---

## 🟡 Medium Priority (Polish & Consistency)

### Web

- [ ] **[style]** Consistent hover/focus states across all buttons
  - Files: `web/components/ui/Button.tsx`, usage across pages
  - Context: Ensure all buttons have proper hover + focus-visible styles
  - Impact: Professional feel, keyboard users know where they are
  - Size: ~35 lines
  - Added: 2026-01-01

- [ ] **[ux]** Confirmation dialog for destructive actions
  - Files: Create `web/components/ui/ConfirmDialog.tsx`, integrate
  - Context: Confirm before deleting groups/expenses
  - Impact: Prevents accidental data loss
  - Size: ~70 lines
  - Added: 2026-01-01

### Mobile

- [ ] **[ux]** Swipe-to-delete for expenses with undo option
  - File: `mobile/screens/GroupDetailsScreen.js`
  - Context: Add swipeable rows with delete action
  - Impact: Quick expense management
  - Size: ~55 lines
  - Added: 2026-01-01

- [ ] **[style]** Haptic feedback on all button presses
  - Files: All button interactions across mobile
  - Context: Add Expo.Haptics.impactAsync(Light) to buttons
  - Impact: Tactile feedback makes app feel responsive
  - Size: ~40 lines
  - Added: 2026-01-01

---

## 🟢 Lower Priority (Nice to Have)

### Web

- [ ] **[ux]** Animated success celebration when settled up
  - File: `web/pages/GroupDetails.tsx`
  - Context: Show confetti or checkmark animation when no debts
  - Impact: Delightful moment, positive reinforcement
  - Size: ~45 lines
  - Added: 2026-01-01

- [ ] **[perf]** Lazy loading + code splitting for routes
  - File: `web/App.tsx`
  - Context: Use React.lazy for page imports
  - Impact: Faster initial load
  - Size: ~30 lines
  - Added: 2026-01-01

### Mobile

- [ ] **[ux]** Biometric authentication option
  - Files: `mobile/context/AuthContext.js`, add local auth
  - Context: FaceID/TouchID for quick login
  - Impact: Faster, more secure login
  - Size: ~70 lines
  - Added: 2026-01-01

---

## ❌ Removed (Too Trivial - Learn from Mistakes)

~~Add single ARIA label to one button~~ - Too small
~~Fix one spacing inconsistency~~ - Too insignificant  
~~Add one hover state~~ - Not comprehensive enough

---

## ✅ Completed Tasks

- [x] **[ux]** Comprehensive empty states with illustrations
  - Completed: 2026-01-01
  - Files modified: `web/components/ui/EmptyState.tsx`, `web/pages/Groups.tsx`, `web/pages/Friends.tsx`
  - Impact: Users now see a polished, illustrated empty state with clear CTAs when they have no groups or friends, instead of plain text.

- [x] **[a11y]** Complete keyboard navigation for Groups page
  - Completed: 2026-01-12
  - File: `web/pages/Groups.tsx`
  - Impact: Users can now navigate groups, join/create buttons, and search using only the keyboard with proper focus indicators.
- [x] **[ux]** Form validation with inline feedback
  - Completed: 2026-01-11
  - Files modified: `web/pages/Auth.tsx`
  - Impact: Users know immediately if input is valid via inline error messages and red borders.

_No tasks completed yet. Move tasks here after completion._
