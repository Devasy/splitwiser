# Palette Journal

## 2025-05-21 - [Feedback on Auth]
**Learning:** Users often click submit multiple times on authentication forms if there's no immediate visual feedback, causing race conditions or frustration.
**Action:** Always add a loading spinner and disable the button immediately upon submission for async auth operations.
