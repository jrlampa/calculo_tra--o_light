/* This code snippet is a test suite written in JavaScript using the Vitest testing framework. It is
testing the functionality of a module related to user experience (UX) funnel instrumentation. Here's
a breakdown of what the code is doing: */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

import {
  UX_FUNNEL_EVENTS,
  setUxFunnelEventCallback,
  buildUxFunnelEvent,
  trackUxFunnelEvent,
} from '@/services/uxFunnelInstrumentation'

describe('uxFunnelInstrumentation', () => {
  let infoSpy
  let errorSpy

  beforeEach(() => {
    infoSpy = vi.spyOn(console, 'info').mockImplementation(() => {})
    errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    setUxFunnelEventCallback(null)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('builds valid funnel event objects', () => {
    const event = buildUxFunnelEvent(UX_FUNNEL_EVENTS.FLOW_STARTED, { origin: 'test' })

    expect(event).toBeTruthy()
    expect(event.name).toBe('flow_started')
    expect(event.properties).toEqual({ origin: 'test' })
    expect(Number.isNaN(Date.parse(event.ts))).toBe(false)
  })

  it('preserves operation and domain identifiers when provided', () => {
    const event = buildUxFunnelEvent(UX_FUNNEL_EVENTS.PERSISTENCE_SAVED, {
      operation_id: '11111111-1111-1111-1111-111111111111',
      projeto_id: '22222222-2222-2222-2222-222222222222',
      ponto_id: '33333333-3333-3333-3333-333333333333',
    })

    expect(event.properties.operation_id).toBe(
      '11111111-1111-1111-1111-111111111111'
    )
    expect(event.properties.projeto_id).toBe(
      '22222222-2222-2222-2222-222222222222'
    )
    expect(event.properties.ponto_id).toBe(
      '33333333-3333-3333-3333-333333333333'
    )
  })

  it('CALCULATION_PERSISTED is a valid event and carries ponto_id', () => {
    const pontoId = '44444444-4444-4444-4444-444444444444'
    const event = buildUxFunnelEvent(UX_FUNNEL_EVENTS.CALCULATION_PERSISTED, {
      ponto_id: pontoId,
      operation_id: 'op-001',
    })

    expect(event).toBeTruthy()
    expect(event.name).toBe('calculation_persisted')
    expect(event.properties.ponto_id).toBe(pontoId)
    expect(event.properties.operation_id).toBe('op-001')
  })

  it('ignores unknown event names', () => {
    const event = trackUxFunnelEvent('not_allowed_event', { foo: 'bar' })

    expect(event).toBeNull()
    expect(infoSpy).not.toHaveBeenCalled()
  })

  it('logs to console and forwards to local callback', () => {
    const callback = vi.fn()
    const cleanup = setUxFunnelEventCallback(callback)

    const event = trackUxFunnelEvent(UX_FUNNEL_EVENTS.PROJECT_CONFIRMED, {
      projeto_id: 1,
      projeto_nome: 'Projeto A',
    })

    expect(infoSpy).toHaveBeenCalledTimes(1)
    expect(callback).toHaveBeenCalledTimes(1)
    expect(callback).toHaveBeenCalledWith(event)

    cleanup()

    trackUxFunnelEvent(UX_FUNNEL_EVENTS.POINT_CONFIRMED, { ponto_id: 2 })
    expect(callback).toHaveBeenCalledTimes(1)
  })

  it('swallows callback exceptions and keeps flow alive', () => {
    setUxFunnelEventCallback(() => {
      throw new Error('callback failed')
    })

    const event = trackUxFunnelEvent(UX_FUNNEL_EVENTS.UNDO_APPLIED, { field_key: 'ang' })

    expect(event).toBeTruthy()
    expect(infoSpy).toHaveBeenCalledTimes(1)
    expect(errorSpy).toHaveBeenCalledTimes(1)
  })
})
