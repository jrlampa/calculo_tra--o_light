export const UX_FUNNEL_EVENTS = Object.freeze({
  FLOW_STARTED: 'flow_started',
  PROJECT_CONFIRMED: 'project_confirmed',
  POINT_CONFIRMED: 'point_confirmed',
  CALCULATION_SUCCEEDED: 'calculation_succeeded',
  PERSISTENCE_SAVED: 'persistence_saved',
  PERSISTENCE_FAILED: 'persistence_failed',
  PERSIST_RETRY_MANUAL: 'persist_retry_manual',
  NEXT_POINT_CLICKED: 'next_point_clicked',
  UNDO_APPLIED: 'undo_applied',
  UNDO_EXPIRED: 'undo_expired',
})

const VALID_EVENT_NAMES = new Set(Object.values(UX_FUNNEL_EVENTS))

let localEventCallback = null

export function setUxFunnelEventCallback(callback) {
  localEventCallback = typeof callback === 'function' ? callback : null
  return () => {
    localEventCallback = null
  }
}

function normalizeProperties(properties) {
  if (!properties || typeof properties !== 'object' || Array.isArray(properties)) {
    return {}
  }
  return properties
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
