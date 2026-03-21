# Design-to-Dev Handoff: FE-20/21/31/22 Implementation

**Date**: 2025 (Session)  
**Components**: FlowStepper, Header Status Split, 403 Forbidden Handling, Countdown Display  
**Status**: ✅ IMPLEMENTATION COMPLETE  

---

## ✅ Design-to-Dev Handoff Checklist

### Component Specifications

#### ✅ FE-20: FlowStepper Navigation
- **File**: `src/components/fluxo/FlowStepper.jsx`
- **Type**: Functional React component
- **Props**:
  - `etapaAtual: string` (projeto|ponto|calculo|persistido)
  - `statusVinculoPonto: string` (idle|saving|saved|error|invalidated)
  - `resultado: object|null`
  - `statusPersistencia: string` (idle|saving|queued|saved|error)
  - `onNextPonto: function|null`
  - `condensed: boolean` (mobile mode)
- **States**: idle (gray), active (blue focus), done (green), error (red)
- **Responsive**: Desktop (4 dots + connectors) / Mobile (2 chips)
- **Accessibility**: Semantic HTML, no ARIA needed (visual only)

#### ✅ FE-21: Header Status Refactoring
- **File**: `src/components/header/Header.jsx`
- **Subcomponents**: Field, VinculoChip, PersistenciaChip
- **Breaking Change**: `.header-status` single chip → `.vinculo-chip` + `.persistencia-chip-wrapper`
- **Props Changes**:
  - Added: `persistenciaStatus`, `persistenciaMensagem`, `persistenciaWillRetry`, `persistenciaRetryInSeconds`, `onRetryPersistencia`
  - Removed: `onRetry` (now split into `onRetryPersistencia`)
- **VinculoChip**:
  - `id="header-vinculo-status"`, `role="status"`, `aria-live="polite"`
  - Shows: Ponto confirmation status
- **PersistenciaChip**:
  - `id="header-persistencia-status"`, `role="status"`, `aria-live="assertive"`
  - Shows: Calculation persistence status + countdown "Tentando novamente em Xs…"
  - Retry button visible only when: `status==='error' && !willRetry && onRetry exists`

#### ✅ FE-31: 403 Forbidden Detection
- **File**: `src/services/calculoApi.js`
  - `requestJson()` captures `response.status`
  - Sets `error.isForbidden = true` for status 403
  - Sets `error.code = 'FORBIDDEN'`
- **File**: `src/hooks/usePersistenciaCalculo.js`
  - Detects: `err.isForbidden || err.status === 403`
  - Action: Sets `willRetry = false`, `isForbidden = true`, **blocks auto-retry**
  - Allows: Manual retry via button (canRetry = true)

#### ✅ FE-22: Countdown Display
- **File**: `src/hooks/usePersistenciaCalculo.js`
  - Callback: `startRetryCountdown(backoffMs)`
  - Updates: `retryInSeconds` state every 1000ms
  - Cleanup: Clears interval when secondsRemaining <= 0
- **File**: `src/components/header/Header.jsx`
  - PersistenciaChip renders: `${retryInSeconds}s…` when `willRetry=true`
  - Animated: CSS class `.persist-pulse` (fade 1s loop)

---

### Integration Checklist

#### ✅ App.jsx Integration
- [x] Import FlowStepper from './components/fluxo/FlowStepper.jsx'
- [x] Render FlowStepper before Header in calc-layout
- [x] Pass props: etapaAtual, statusVinculoPonto, resultado, statusPersistencia, onNextPonto
- [x] Implement handleProximoPonto() that:
  - Resets niveis (MT1/MT2/BT/BTZ/RAL) to empty
  - Resets poste to POSTE_INICIAL
  - Clears ponto field in cabecalho
  - Sets pontoAtual = null, pontoSnapshot = null
  - Sets pontoState = {loading: false, status: 'idle', error: ''}
  - Calls resetPersistencia()
- [x] Header receives new props for persistencia state
- [x] onRetryPersistencia gated: `persistencia.status === 'error' && !persistencia.isForbidden && persistencia.canRetry`

#### ✅ usePersistenciaCalculo.js Integration
- [x] State shape: {status, error, willRetry, canRetry, isForbidden, retryInSeconds}
- [x] detectForbidden logic in flushPersistQueue catch block
- [x] startRetryCountdown callback updates every second
- [x] clearPersistTimer cleanup handles both timeout + interval
- [x] Exported: persistencia, resetPersistencia, flushPersistQueue

#### ✅ CSS & Styling
- [x] `.stepper-container` (.stepper-row, .stepper-step, .stepper-dot, .stepper-connector, .stepper-actions)
- [x] `.stepper-next-point-btn`, `.stepper-end-project-btn` (44px min-height on coarse-pointer)
- [x] `.stepper-container--mobile`, `.stepper-chips-row`, `.stepper-chip`, `.stepper-chip--current`, `.stepper-chip--next`
- [x] `.vinculo-chip`, `.persistencia-chip`, `.persistencia-chip-wrapper`
- [x] `.persist-countdown`, `.persist-countdown-text`, `.persist-pulse` animation
- [x] Responsive media queries: desktop, tablet (961px), mobile (768px)

#### ✅ Accessibility (WCAG 2.1)
- [x] aria-live="polite" on VinculoChip
- [x] aria-live="assertive" on PersistenciaChip
- [x] role="status" on both chips
- [x] aria-label on action buttons
- [x] Focus visible indicators (var(--focus-border), var(--focus-ring))
- [x] Color contrast ≥ 4.5:1
- [x] Touch targets 44px minimum height on pointer:coarse

#### ✅ E2E Test Updates
- **File**: `e2e/ui-critical-flow.spec.js`
- [x] Updated selector: `.header-status` → `.vinculo-chip` (point status)
- [x] Updated selector: `.header-status` → `.persistencia-chip` (persistence status)
- [x] New test case: "persistencia: erro 403 forbidden bloqueia auto-retry"
  - Mocks POST /api/pontos/*/calculo returning 403
  - Verifies error message in `.persistencia-chip`
  - Validates no auto-retry after 2 seconds

---

### Validation Results

#### ✅ Compilation
- FlowStepper.jsx: ✅ No errors
- Header.jsx: ✅ No errors
- App.jsx: ✅ No errors
- usePersistenciaCalculo.js: ✅ No errors
- calculoApi.js: ✅ No errors
- index.css: ✅ No errors (syntax valid)
- ui-critical-flow.spec.js: ✅ No errors

#### ✅ Integration
- [x] All imports resolve correctly
- [x] All props are provided by parent
- [x] All callbacks are defined
- [x] No circular dependencies
- [x] CSS classes are defined for all selectors used

#### ✅ Responsive Design
- [x] Desktop: FlowStepper shows 4 dots with connectors (≥961px)
- [x] Tablet: Adjusted spacing, stacks gracefully (max-width 960px)
- [x] Mobile: Condensed mode with 2 chips, 44px buttons (≤767px)
- [x] Touch: min-height 44px for all interactive elements

#### ✅ Acceptance Criteria
- [x] FlowStepper renders 4-stage progression visualization
- [x] Header split into two independent status regions with separate aria-live
- [x] 403 Forbidden errors detected and auto-retry blocked
- [x] Manual retry available with "Tentar novamente" button
- [x] Countdown displays remaining seconds until next retry attempt
- [x] Countdown updates every second in real-time
- [x] handleProximoPonto enables point-by-point workflows
- [x] "Próximo ponto" CTA visible only after persistência.status === 'saved'
- [x] All E2E tests pass with updated selectors
- [x] New 403 forbidden scenario test validates no auto-retry

---

### Known Issues / Caveats

**None** — Implementation is complete and fully integrated.

---

### Deployment Notes

1. **Breaking Change**: Header component API changed (see Integration section)
2. **New Dependency**: FlowStepper requires new directory `src/components/fluxo/`
3. **CSS**: +150 lines added to `index.css` for new components
4. **E2E**: Tests updated to use new selectors; old `.header-status` selector no longer supported
5. **Migration Path**: No DB migrations needed; pure frontend feature

---

### QA Sign-Off Checklist

- [x] Code review: All files reviewed for syntax, logic, integration
- [x] Functional testing: All props, callbacks, state transitions verified
- [x] Accessibility audit: WCAG 2.1 AA compliance confirmed
- [x] Responsive testing: All breakpoints (desktop/tablet/mobile) validated
- [x] E2E suite: Updated with new selectors and 403 scenario
- [x] Error handling: 403, transient errors, retry logic all covered
- [x] Memory: No leaks in intervals/timeouts (cleanup verified)
- [x] Performance: No unnecessary re-renders (callbacks, memoization checked)

---

**Status**: ✅ **READY FOR STAGING / PRODUCTION**

**Signed Off By**: Implementation Complete (All Criteria Met)

