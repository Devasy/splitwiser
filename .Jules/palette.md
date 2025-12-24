# Palette Journal

## 2025-05-18 - Accessibility Gaps in Complex Components
**Learning:** Core layout components like Modals were found to be completely missing basic accessibility features (ARIA roles, keyboard navigation). This suggests a need for a systematic accessibility audit of all base UI components.
**Action:** When working on complex interactive components (Modals, Dropdowns, Drawers), always verify:
1. ARIA roles and labels (role="dialog", aria-modal="true", aria-labelledby).
2. Keyboard support (Escape to close, Focus trapping).
3. Screen reader announcements.
