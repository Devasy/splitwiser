# Palette Journal

## 2024-05-22 - Standardized Button Loading State
**Learning:** The application previously used manual text updates (e.g., "Processing...") for loading states, which causes layout shifts and lacks visual consistency.
**Action:** Implemented a standardized `isLoading` prop on the `Button` component that automatically disables the button and renders a `Spinner`. This pattern should be used for all async actions going forward to ensure a consistent Neobrutalism look and prevent multiple submissions.
