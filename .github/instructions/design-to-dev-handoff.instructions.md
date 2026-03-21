---
name: "Design to Dev Handoff Checklist"
description: "Use when: handing off UI/UX decisions to development, defining acceptance criteria, and validating a11y, responsiveness, UI states, and UX metrics"
applyTo:
  - "src/**/*.{js,jsx,ts,tsx,css}"
  - "app/**/*.{js,jsx,ts,tsx,css}"
  - "pages/**/*.{js,jsx,ts,tsx,css}"
  - "components/**/*.{js,jsx,ts,tsx,css}"
  - "**/*.md"
---
# Design-to-Dev Handoff

Apply this checklist whenever a design proposal is turned into implementation tasks.

## Mandatory Handoff Content
- Objective: user goal, business goal, and success criteria.
- Scope: screens, components, states, and constraints.
- Interaction model: main flow, alternates, and error recovery.
- Visual system: tokens, typography scale, spacing rules, and icon usage.

## Required Checklist (Do Not Skip)

### 1. Accessibility (a11y)
- Contrast compliance for text and interactive controls.
- Keyboard navigation and visible focus states.
- Semantic labels, roles, and assistive text.
- Error messages linked to inputs and announced clearly.

### 2. Responsiveness
- Explicit behavior for Desktop, Tablet, and Mobile.
- Grid/breakpoint strategy and component reflow rules.
- Touch target size and spacing for mobile interactions.

### 3. UI States
- Loading, empty, error, and success states are specified.
- Disabled/hover/focus/pressed states for interactive controls.
- API failure fallback and retry behavior are documented.

### 4. UX Metrics
- Define measurement plan for:
  - Task success rate
  - Time on task
  - Drop-off rate
- Include event instrumentation points and naming guidance.

## Delivery Format
- Use concise acceptance criteria per component/flow.
- Include implementation hints that reduce ambiguity.
- If any checklist item is missing, block sign-off and report the gap.
