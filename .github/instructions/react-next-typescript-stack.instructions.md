---
name: "React Next TypeScript Stack Conventions"
description: "Use when: React, Next.js, TypeScript, hooks, tailwind, vitest, react testing library, playwright"
applyTo:
  - "src/**/*.{js,jsx,ts,tsx}"
  - "app/**/*.{js,jsx,ts,tsx}"
  - "pages/**/*.{js,jsx,ts,tsx}"
  - "components/**/*.{js,jsx,ts,tsx}"
  - "e2e/**/*.{js,jsx,ts,tsx}"
---
# React Next TypeScript Conventions

Apply these defaults automatically for frontend work. Do not ask which baseline structure to use unless a direct conflict exists with current code.

## Component and Logic Style
- Prefer Functional Components.
- Keep business logic in custom hooks and service helpers.
- Keep UI components focused on rendering and interactions.

## Architecture
- Use Folder-by-Feature by default for new modules.
- Use Atomic Design only when the current project already follows it.
- Keep shared UI and domain-level logic separated.

## Styling
- Use Tailwind CSS.
- Prioritize accessibility: semantic HTML, keyboard navigation, labels, and color contrast.
- Ensure responsive behavior for mobile and desktop breakpoints.

## Testing Rules
- Use Vitest + React Testing Library for behavior-focused unit/integration tests.
- Use Playwright for critical E2E flows.
- Test user-visible behavior and failure states, not implementation details.

## Performance
- Prevent unnecessary rerenders with memoization when justified (`React.memo`, `useMemo`, `useCallback`).
- Split heavy components and defer expensive work where possible.