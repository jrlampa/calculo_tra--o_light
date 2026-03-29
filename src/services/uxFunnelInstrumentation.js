/**
 * The above JavaScript code defines a module for tracking user experience funnel events and allows
 * setting a callback function to handle these events.
 * @param properties - The `properties` parameter in the code snippet refers to additional data that
 * can be associated with a specific UX funnel event. These properties provide more context or details
 * about the event being tracked. The `normalizeProperties` function ensures that the properties are in
 * the correct format before being included in the event object.
 * @returns The code snippet provided defines a set of UX funnel events, a set of valid event names,
 * functions to set a callback for UX funnel events, normalize properties, build a UX funnel event
 * object, and track a UX funnel event.
 */
export const UX_FUNNEL_EVENTS = Object.freeze({
  FLOW_STARTED: 'flow_started',
  PROJECT_CONFIRMED: 'project_confirmed',
  POINT_CONFIRMED: 'point_confirmed',
  CALCULATION_SUCCEEDED: 'calculation_succeeded',
  PERSISTENCE_SAVED: 'persistence_saved',
  CALCULATION_PERSISTED: 'calculation_persisted',
  PERSISTENCE_FAILED: 'persistence_failed',
  PERSIST_RETRY_MANUAL: 'persist_retry_manual',
  NEXT_POINT_CLICKED: 'next_point_clicked',
  UNDO_APPLIED: 'undo_applied',
  UNDO_EXPIRED: 'undo_expired',
  BATCH_SAVE_START: 'batch_save_start',
  BATCH_SAVE_SUCCESS: 'batch_save_success',
  BATCH_SAVE_ERROR: 'batch_save_error',
  BATCH_SAVE_FAILED: 'batch_save_failed',
  NEW_PROJECT_STARTED_LOCAL: 'new_project_started_local',
  PROJECT_OPENED_FROM_DB: 'project_opened_from_db',
  PROJECT_DELETED_FROM_DB: 'project_deleted_from_db',
  IMPORT_EXCEL_STARTED: 'import_excel_started',
  IMPORT_EXCEL_SUCCESS: 'import_excel_success',
  IMPORT_EXCEL_FAILED: 'import_excel_failed',
  CLEAR_STARTED: 'clear_started',
  CLEAR_COMMITTED: 'clear_committed',
  CLEAR_UNDONE: 'clear_undone',
})

const VALID_EVENT_NAMES = new Set(Object.values(UX_FUNNEL_EVENTS))

let localEventCallback = null

// In-memory ring-buffer of the last MAX_LOG_ENTRIES events for audit/traceability.
// 200 entries covers a full working session. With ~12 distinct event types the
// real per-point event count depends on retry paths and batch ops; in practice
// a typical point produces 3-5 events (confirmed, calculated, persisted ± retry).
// 200 gives headroom for ~40-65 points per session without memory pressure.
// Exposed via getTraceabilityLog() so callers can collect evidence without a
// persistent backend.
const MAX_LOG_ENTRIES = 200
const _eventLog = []

export function setUxFunnelEventCallback(callback) {
  localEventCallback = typeof callback === 'function' ? callback : null
  return () => {
    localEventCallback = null
  }
}

/**
 * Returns a snapshot of the most recent UX funnel events (up to MAX_LOG_ENTRIES).
 * Each entry has the shape: { name, ts, properties }.
 *
 * Useful for producing an in-session audit trail that maps to sections 9 and 10
 * of the QA checklist (rastreabilidade por operação).
 *
 * @returns {Array<{name: string, ts: string, properties: object}>}
 */
export function getTraceabilityLog() {
  return _eventLog.slice()
}

/** Clears the in-memory event log (intended for use in tests). */
export function clearTraceabilityLog() {
  _eventLog.length = 0
}

function normalizeProperties(properties) {
  if (!properties || typeof properties !== 'object' || Array.isArray(properties)) {
    return {}
  }

  const normalized = { ...properties }
  if ('operation_id' in normalized) {
    normalized.operation_id = normalized.operation_id || null
  }
  if ('projeto_id' in normalized) {
    normalized.projeto_id = normalized.projeto_id || null
  }
  if ('ponto_id' in normalized) {
    normalized.ponto_id = normalized.ponto_id || null
  }
  return normalized
}

export function buildUxFunnelEvent(eventName, properties = {}) {
  if (!VALID_EVENT_NAMES.has(eventName)) {
    return null
  }

  return {
    name: eventName,
    ts: new Date().toISOString(),
    properties: normalizeProperties(properties),
  }
}

export function trackUxFunnelEvent(eventName, properties = {}) {
  const event = buildUxFunnelEvent(eventName, properties)
  if (!event) {
    return null
  }

  // Append to ring-buffer (trim oldest when full)
  _eventLog.push(event)
  if (_eventLog.length > MAX_LOG_ENTRIES) { _eventLog.shift() }

  console.info('[ux-funnel]', event)

  if (localEventCallback) {
    try {
      localEventCallback(event)
    } catch (err) {
      console.error('[ux-funnel] local callback failed', err)
    }
  }

  return event
}
