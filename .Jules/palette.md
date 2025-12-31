# Palette Journal

## 2024-05-22 - Password Toggles and Label Selectors
**Learning:** When implementing "Show/Hide Password" toggles within an input field, simply adding an icon button can create ambiguity for automated testing tools if not careful. While `htmlFor`/`id` binding connects the visual label to the input correctly, the toggle button's `aria-label` (e.g., "Show password") contains the same keyword ("password") as the main label.
**Action:** Always prefer selecting by strict label text or using specific input types (`input[type='password']`) in tests when a field has auxiliary interactive controls containing similar accessible names. Ensure the toggle button is clearly distinct from the input itself in the accessibility tree.
