# Jules Knowledge Base

> Learnings, patterns, and solutions discovered while working on Splitwiser UI/UX.

---

## Project Architecture

### Web Application Structure
**Date:** 2026-01-01
**Context:** Initial codebase analysis

The web app follows a clean architecture:
```
web/
├── App.tsx           # Main router with protected routes
├── components/
│   ├── layout/       # Layout, Sidebar, ThemeWrapper
│   └── ui/           # Reusable: Button, Card, Input, Modal, Skeleton, Toast
├── contexts/         # AuthContext, ThemeContext, ToastContext
├── pages/            # Route pages
├── services/         # API calls
├── constants.ts      # Theme constants (GLASSMORPHISM, NEOBRUTALISM)
└── types.ts          # TypeScript interfaces
```

### Mobile Application Structure
**Date:** 2026-01-01
**Context:** Initial codebase analysis

The mobile app uses Expo with React Navigation:

```
mobile/
├── App.js            # Entry point with providers
├── screens/          # All screen components
├── navigation/       # Stack and Tab navigators
├── context/          # AuthContext
├── api/              # API client and service functions
└── utils/            # Helpers (currency, balance calculations)
```

---

## Theming System

### Web Dual-Theme Pattern
**Date:** 2026-01-01
**Context:** Understanding theme-switching mechanism

The web app supports two themes controlled by `ThemeContext`:
- **GLASSMORPHISM**: Modern, translucent look with blurs and gradients
- **NEOBRUTALISM**: Bold, sharp design with hard shadows and borders

**How to implement:**
```tsx
const { style, mode } = useTheme();
const isNeo = style === THEMES.NEOBRUTALISM;

// Apply conditional classes
className={isNeo 
  ? 'border-2 border-black rounded-none shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]' 
  : 'rounded-xl backdrop-blur-md border-white/20'
}
```

**Important:** Always support BOTH themes when modifying UI components.

### Color Tokens

**Date:** 2026-01-01
**Context:** Custom colors in tailwind.config.js

```js
colors: {
  neo: {
    main: '#8855ff',    // Primary purple
    second: '#ff9900',  // Secondary orange
    accent: '#00cc88',  // Accent green
    bg: '#f0f0f0',      // Background light
    dark: '#1a1a1a'     // Background dark
  }
}
```

---

## Component Patterns

### Toast Notifications

**Date:** 2026-01-07
**Context:** Implemented Toast system

The app uses a global `ToastProvider` in `App.tsx` and a `useToast` hook.

**Usage:**
```tsx
const { addToast } = useToast();
addToast('Success message', 'success'); // Types: 'success' | 'error' | 'info'
```

**Implementation:**
- `ToastContainer` is rendered once in `ToastProvider`.
- Uses `z-100` to sit above Modals (`z-50`).
- Supports both Glassmorphism and Neobrutalism themes.

### Button Component Variants

**Date:** 2026-01-01
**Context:** Understanding Button.tsx API

```tsx
<Button 
  variant="primary|secondary|danger|ghost"
  size="sm|md|lg"
  onClick={handler}
  disabled={boolean}
  className="additional classes"
>
  Content
</Button>
```

### Card Component with Title/Action

**Date:** 2026-01-01
**Context:** Card.tsx supports optional header

```tsx
<Card 
  title="Optional Title"
  action={<Button>Action</Button>}
  className="additional"
>
  {children}
</Card>
```

### Modal Component Pattern

**Date:** 2026-01-01
**Context:** Modal.tsx structure

```tsx
<Modal
  isOpen={boolean}
  onClose={handler}
  title="Modal Title"
  footer={<>Cancel and Submit buttons</>}
>
  {content}
</Modal>
```

---

## Mobile Patterns

### React Native Paper Components

**Date:** 2026-01-01
**Context:** Primary UI library for mobile

Commonly used components:
- `<Card>` with `<Card.Title>` and `<Card.Content>`
- `<Avatar.Image>` and `<Avatar.Text>`
- `<Button mode="contained|outlined|text">`
- `<TextInput>` with label, value, onChangeText
- `<FAB>` for floating action buttons
- `<Portal>` and `<Modal>` for overlays
- `<ActivityIndicator>` for loading states

### Safe Area Pattern

**Date:** 2026-01-01
**Context:** Screens use View without SafeAreaView

Most screens use `<View style={{ flex: 1 }}>` - consider wrapping in `SafeAreaView` for notched devices.

---

## API Response Patterns

### Groups API

**Date:** 2026-01-01
**Context:** Group data structure from backend

```typescript
interface Group {
  _id: string;
  name: string;
  currency: string;
  joinCode: string;
  imageUrl?: string;
  members: GroupMember[];
  createdAt: string;
}
```

### Balance Summary API

**Date:** 2026-01-01
**Context:** Dashboard balance data

```typescript
interface BalanceSummary {
  totalOwedToYou: number;
  totalYouOwe: number;
  netBalance: number;
  groupsSummary: GroupBalanceSummary[];
}
```

---

## Known Issues & Gotchas

### Image URL Validation

**Date:** 2026-01-01
**Context:** Avatar image handling pattern

Both web and mobile use this pattern to validate image URLs:
```javascript
const isImage = imageUrl && /^(https?:|data:image)/.test(imageUrl);
```

Always check before rendering `<img>` or `<Avatar.Image>`.

### Currency Formatting

**Date:** 2026-01-01
**Context:** Mobile uses utility, web uses inline

- Mobile: Uses `formatCurrency()` and `getCurrencySymbol()` from `utils/currency.js`
- Web: Uses inline template literals like `${group.currency} ${amount.toFixed(2)}`

**Consider:** Standardizing currency formatting across platforms.

### Framer Motion in Web

**Date:** 2026-01-01
**Context:** Animation library usage

Common patterns:

```tsx
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  whileHover={{ scale: 1.02 }}
  transition={{ type: 'spring', stiffness: 100 }}
/>
```

Use `AnimatePresence` for exit animations.

---

## Best Practices Learned

### 1. Accessibility First

Always add:
- `aria-label` for icon-only buttons
- `role` attributes for non-semantic elements
- `tabIndex` for keyboard navigation
- Focus styles for keyboard users

### 2. Loading State Hierarchy

1. Full-screen skeleton for initial load
2. Inline loading for actions
3. Optimistic updates where possible

### 3. Error Handling

1. Try/catch API calls
2. Show user-friendly error messages
3. Log errors for debugging
4. Provide retry options

### 4. Responsive Breakpoints

Tailwind breakpoints used:
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px

---

## Errors Encountered & Solutions

### Previous Agent Mistakes (Lessons Learned)

**Date:** 2026-01-01
**Context:** Learning from past "Palette" agent that didn't work well

**Mistake 1: Wrong Package Manager**

- **Error:** Agent used `pnpm` commands when project uses `npm`
- **Root Cause:** Didn't verify tooling from package.json/lock files
- **Solution:** Always check for package-lock.json (npm), yarn.lock (yarn), or pnpm-lock.yaml (pnpm) FIRST
- **Verification:** `ls package*.json` and check for lock files

**Mistake 2: Changes Too Trivial**

- **Error:** Made insignificant changes like single ARIA labels that users didn't notice
- **Root Cause:** Over-cautious approach with "under 50 lines" hard limit
- **Solution:** Aim for 30-100 lines of meaningful, focused change. Each commit should be user-noticeable.
- **Example of Good Change:** Implement complete skeleton loading system, not just one skeleton

**Mistake 3: Misaligned with Project Direction**

- **Error:** Made generic UX improvements without understanding Splitwiser's goals
- **Root Cause:** Didn't read README or understand project trajectory
- **Solution:** Check README, recent commits, issues. Understand Splitwiser = modern expense-splitting with dual-theme excellence

**Files to Check Before Starting:**

- `README.md` - Project vision
- `package.json` - Available scripts and tooling
- `.git/logs/HEAD` or recent commits - Development direction

---

## Project Direction & Goals

### What Splitwiser Is About

**Date:** 2026-01-01

Splitwiser is focused on (per README):
1. **Modern expense splitting** - Making group expenses effortless
2. **Group management** - Create and manage expense groups
3. **Real-time synchronization** - Keep data synced across devices
4. **Secure authentication** - JWT-based auth with refresh tokens
5. **Receipt management** - Track and store receipt images
6. **Debt simplification** - Minimize number of transactions
7. **Multi-currency support** - Handle different currencies
8. **Exceptional UX** - Beautiful, intuitive, delightful interactions
9. **Cross-platform** - Web (React/Vite/TypeScript) and mobile (Expo/React Native)

**Current Implementation Details:**
- Web app uses dual-theme design system (Glassmorphism & Neobrutalism)
- Mobile uses React Native Paper (Material Design)
- Backend: FastAPI + MongoDB

**NOT focused on:**
- Generic business app features
- Traditional accounting workflows
- Enterprise features
- One-off utilities

**When picking tasks, ask:**
- Does this improve expense splitting experience?
- For web: Does it work in BOTH themes?
- Will users notice and appreciate this?
- Does it align with the README's core features?

---

_Document errors and their solutions here as you encounter them._

```markdown
<!-- Template for documenting errors:
### Error: [Error Name]
**Date:** YYYY-MM-DD
**Context:** What you were trying to do
**Error Message:** The actual error
**Solution:** How you fixed it
**Files Affected:** List of files
-->
```

---

## Dependencies Reference

### Web

- react-router-dom: Routing
- framer-motion: Animations
- recharts: Charts in Dashboard
- lucide-react: Icons
- tailwindcss: Styling

### Mobile

- @react-navigation/*: Navigation
- react-native-paper: UI components
- axios: API calls (via api/client.js)
- expo: Platform SDK
