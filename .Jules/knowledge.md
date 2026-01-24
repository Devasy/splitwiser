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
│   └── ui/           # Reusable: Button, Card, Input, Modal, Skeleton
├── contexts/         # AuthContext, ThemeContext
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

### Error Boundary Pattern

**Date:** 2026-01-14
**Context:** Implementing global error handling

React Error Boundaries must be class components to use `componentDidCatch`. However, to use hooks (like `useTheme` or `useNavigate`), you should split the fallback UI into a separate functional component.

```tsx
// 1. Functional Fallback (uses hooks)
const ErrorFallback = ({ error, resetErrorBoundary }) => {
  const { style } = useTheme();
  return <div className={style...}>...</div>;
}

// 2. Class Boundary (handles logic)
class ErrorBoundary extends Component {
  render() {
    if (this.state.hasError) {
      return <ErrorFallback ... />;
    }
    return this.props.children;
  }
}
```

**Testing Tip:** React Error Boundaries do **not** catch errors in event handlers. To verify them, you must throw inside the `render` method (e.g., `if (shouldThrow) throw new Error()`).

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

### Clickable Cards & Accessibility

**Date:** 2026-01-01
**Context:** Making `motion.div` or non-button elements accessible

When making a div clickable (like a card), you must ensure it's accessible:
1.  **Role**: Add `role="button"`.
2.  **TabIndex**: Add `tabIndex={0}` so it's focusable.
3.  **Keyboard Handler**: Add `onKeyDown` to handle 'Enter' and 'Space'.
4.  **Label**: Add `aria-label` to describe the action.
5.  **Focus Styles**: Add visible focus styles (e.g., `focus:ring`).

```tsx
<motion.div
  onClick={handleClick}
  role="button"
  tabIndex={0}
  aria-label="View Details"
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  }}
  className="... focus:outline-none focus:ring-4 focus:ring-blue-500"
>
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

### Toast Notification Pattern

**Date:** 2026-01-01
**Context:** ToastContext.tsx and Toast.tsx

```tsx
const { addToast } = useToast();
addToast('Message', 'success|error|info');
```

- Supports `success`, `error`, `info` types
- Automatically adapts to current theme (Glassmorphism/Neobrutalism)
- Auto-dismisses after 3 seconds
- Stacks vertically in bottom-right

### Confirmation Dialog Pattern

**Date:** 2026-01-14
**Context:** Replacing window.confirm with custom modal

```tsx
const { confirm } = useConfirm();

// In async handler
if (await confirm({
  title: 'Delete Item',
  message: 'Are you sure?',
  variant: 'danger',
  confirmText: 'Delete'
})) {
  // Proceed with deletion
}
```

- Promise-based API avoids callback hell
- Supports `danger` and `primary` variants
- Fully accessible with `role="dialog"`

### Form Validation Pattern

**Date:** 2026-01-01
**Context:** Implemented in Auth.tsx

```tsx
type FormErrors = { [key: string]: string };
const [fieldErrors, setFieldErrors] = useState<FormErrors>({});

// 1. Validation Logic
const validate = () => {
  const newErrors: FormErrors = {};
  if (!email) newErrors.email = 'Required';
  setFieldErrors(newErrors);
  return Object.keys(newErrors).length === 0;
};

// 2. Clear on type
const clearFieldError = (field: string) => {
  if (fieldErrors[field]) {
    setFieldErrors(prev => ({ ...prev, [field]: undefined }));
  }
};

// 3. Render with accessibility
<form onSubmit={handleSubmit} noValidate>
  <Input
    error={fieldErrors.email}
    onChange={(e) => {
      setEmail(e.target.value);
      clearFieldError('email');
    }}
    // Input component handles:
    // aria-invalid={!!error}
    // aria-describedby={`${id}-error`}
    // Error message has id={`${id}-error`} and role="alert"
  />
</form>
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

## Testing & Verification

### Playwright Verification Patterns
**Date:** 2026-01-01
**Context:** Verifying accessibility changes with Playwright scripts

When writing Playwright scripts to verify frontend changes without backend:

1. **Auth Mocking:** You must mock `/users/me` persistently. If this call fails or returns 401, `AuthContext` will force a redirect to login, breaking navigation tests.
2. **Route Matching:** Use specific route patterns (e.g., `**/users/me`) and ensure they don't accidentally swallow longer paths (like `**/users/me/balance-summary`) if using wildcards carelessly. Register specific paths before general ones if using `page.route` order dependence, or use specific globs.
3. **Response Structure:** Mocks must match the structure expected by `axios` interceptors and components. If `axios` returns `res.data` as the body, and the component expects `res.data.groups`, the mock body should be `{"groups": [...]}` (not `{"data": {"groups": ...}}`).

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

## Recent Implementation Reviews

### ✅ Successful PR Pattern: Error Boundary (#240)

**Date:** 2026-01-14
**Context:** Implementing global error handling

**What was implemented:**
1. Created `ErrorBoundary.tsx` with class component + functional fallback.
2. Wrapped `AppRoutes` in `App.tsx` with `ErrorBoundary`.
3. Styled fallback UI for both Neobrutalism and Glassmorphism.
4. Added "Retry" and "Go Home" options.

**Why it succeeded:**
- ✅ Complete system (Component + Integration + Styling).
- ✅ Solved "React Hooks inside Class Component" by splitting logic.
- ✅ Verified using a temporary render-phase throw (not event handler).
- ✅ Maintained dual-theme support.

**Key learnings:**
- Error Boundaries only catch errors in Render/Lifecycle, NOT event handlers.
- Verification requires triggering an error during render (e.g., conditional throw).
- Must wrap Router if using `useNavigate` or `Link` in fallback.

---

### ✅ Successful PR Pattern: Toast Notification System (#227)

**Date:** 2026-01-13
**Context:** Review of merged async agent PRs

**What was implemented:**
1. Created `ToastContext` with proper state management
2. Created `Toast` component with dual-theme support
3. Integrated `ToastProvider` into `App.tsx`
4. Added toast notifications to:
   - Auth.tsx (login/signup feedback)
   - Groups.tsx (create/join group)
   - GroupDetails.tsx (expense C/U/D, payments, settings)
   - Profile.tsx (profile updates)

**Why it succeeded:**
- ✅ Complete system implementation (not piecemeal)
- ✅ Dual-theme support from the start
- ✅ Proper accessibility (aria-label on close button)
- ✅ Memory leak prevention (useEffect cleanup in ToastItem)
- ✅ Integrated across multiple pages immediately
- ✅ Auto-dismiss with configurable duration

**Key learnings:**
- Always implement complete systems with all integration points
- Build theme support into components from the start
- Consider memory management (cleanup timers properly)
- Integrate broadly - don't just add to one page

**Files Modified:**
- `web/contexts/ToastContext.tsx` (created)
- `web/components/ui/Toast.tsx` (created)
- `web/App.tsx` (added provider)
- `web/pages/Auth.tsx`, `web/pages/Groups.tsx`, `web/pages/GroupDetails.tsx`, `web/pages/Profile.tsx` (integrated)

---

### ✅ Successful PR Pattern: Keyboard Navigation Iteration (#236)

**Date:** 2026-01-13
**Context:** Review of merged async agent PRs

**What was implemented:**
- Commit 1: Added manual keyboard handlers to group cards (working solution)
- Commit 2: Refactored to semantic `motion.button` (better solution)

**Implementation evolution:**
```tsx
// Iteration 1: Manual handlers
<motion.div
  onClick={...}
  role="button"
  tabIndex={0}
  onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') ... }}
>

// Iteration 2: Semantic element
<motion.button
  onClick={...}
  aria-label="..."
  className="w-full text-left"
>
```

**Why it succeeded:**
- ✅ Shipped working solution first
- ✅ Recognized better semantic approach
- ✅ Made refinement commit to improve
- ✅ Added search input aria-label too
- ✅ Added focus ring styles

**Key learnings:**
- Don't be afraid to iterate and refine
- Semantic HTML > ARIA when possible
- Ship working code, then improve it
- Two focused commits better than one sprawling commit

---

### ✅ Successful PR Pattern: Form Validation with A11y (#234)

**Date:** 2026-01-13
**Context:** Review of merged async agent PRs

**What was implemented:**
1. Added validation logic (email regex, password length, required fields)
2. Added field-level error state management
3. Clear errors on field change (good UX)
4. Proper accessibility attributes throughout
5. Added `noValidate` to form (custom validation)
6. Clear errors when switching between login/signup

**Accessibility done right:**
- Input component handles `aria-invalid`
- Input component handles `aria-describedby` for errors
- Error messages have `role="alert"`
- Server errors also have `role="alert"`

**Why it succeeded:**
- ✅ Complete validation system
- ✅ Accessibility considered from start
- ✅ Good UX (clear errors on type)
- ✅ Works with existing Input component
- ✅ Handles both client and server errors

**Key learnings:**
- Build accessibility in from the start
- Leverage existing components (Input already had error prop)
- Think about user flow (clear errors on type, on mode switch)

---

### ✅ Successful PR Pattern: EmptyState Component (#226)

**Date:** 2026-01-13
**Context:** Review of merged async agent PRs

**What was implemented:**
1. Created reusable `EmptyState` component
2. Built-in dual-theme support
3. Added `aria-hidden="true"` to decorative icon
4. Integrated into Groups and Friends pages

**Why it succeeded:**
- ✅ Reusable component created
- ✅ Dual-theme support built-in
- ✅ Proper accessibility (aria-hidden for decorative)
- ✅ Used immediately in two places

**Key learnings:**
- Create reusable components when pattern repeats
- Always consider decorative vs meaningful content
- Integrate immediately to prove usefulness

---

### ✅ Successful PR Pattern: Dashboard Skeleton (#225)

**Date:** 2026-01-13
**Context:** Review of merged async agent PRs

**What was implemented:**
1. Created `DashboardSkeleton` component
2. Mimics actual dashboard layout (cards + chart area)
3. Replaced simple "Loading..." text
4. Proper Tailwind animation classes

**Why it succeeded:**
- ✅ Improves perceived performance
- ✅ Reduces layout shift
- ✅ Professional loading experience
- ✅ Matches actual layout

**Key learnings:**
- Skeleton loaders should match actual content layout
- Use existing Tailwind animation utilities
- Better than generic spinners for content-heavy pages

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
