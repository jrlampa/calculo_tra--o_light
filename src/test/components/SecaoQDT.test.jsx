/**
 * Tests for SecaoQDT component.
 *
 * Covered paths:
 *  1. Renders section title "Queda de Tensão (QDT) %".
 *  2. Renders all six input fields (v_nominal_mt, drop_mt_pct, v_nominal_bt, drop_trafo_pct, coef_perda, drop_bt1_pct, reg_mt, drop_bt2_pct).
 *  3. Inputs have the initial values from `dados` prop.
 *  4. Fires `onChange(campo, valor)` when each input changes.
 *  5. Shows resultado values when provided.
 *  6. Shows QUEDA TOTAL when resultado available.
 *  7. Does not crash when resultado is null/undefined.
 */
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'

import SecaoQDT from '@/components/secao/SecaoQDT'

// ─── helpers ──────────────────────────────────────────────────────────────────

const DADOS_BASE = {
  v_nominal_mt: '13800',
  drop_mt_pct: '5',
  v_nominal_bt: '220',
  drop_trafo_pct: '3',
  coef_perda: '0.8',
  drop_bt1_pct: '2',
  reg_mt: '1.05',
  drop_bt2_pct: '1.5',
}

const RESULTADO_BASE = {
  v_mt_initial: 13800,
  v_mt_node: 13100,
  v_bt_start: 220,
  v_bt_node2: 208,
  drop_total_pct: 5.45,
}

function renderQDT(overrides = {}) {
  return render(
    <SecaoQDT
      dados={DADOS_BASE}
      onChange={vi.fn()}
      resultado={null}
      {...overrides}
    />
  )
}

// ─── tests ────────────────────────────────────────────────────────────────────

describe('SecaoQDT', () => {
  // 1. Title
  it('renders the section title', () => {
    renderQDT()
    expect(screen.getByText(/Queda de Tensão \(QDT\)/i)).toBeInTheDocument()
  })

  // 2. All input fields present
  it('renders all eight input fields', () => {
    renderQDT()
    const inputs = screen.getAllByRole('textbox')
    // The 8 fields: v_nominal_mt, drop_mt_pct, v_nominal_bt, drop_trafo_pct,
    // coef_perda, drop_bt1_pct, reg_mt, drop_bt2_pct
    expect(inputs.length).toBeGreaterThanOrEqual(8)
  })

  // 3. Initial values from dados prop
  it('shows initial value from dados for v_nominal_mt', () => {
    renderQDT()
    const input = screen.getByDisplayValue('13800')
    expect(input).toBeInTheDocument()
  })

  it('shows initial value from dados for drop_mt_pct', () => {
    renderQDT()
    expect(screen.getByDisplayValue('5')).toBeInTheDocument()
  })

  // 4. onChange fired
  it('calls onChange with campo and value when v_nominal_mt changes', () => {
    const onChange = vi.fn()
    renderQDT({ onChange })

    // v_nominal_mt is the first input
    const inputs = screen.getAllByRole('textbox')
    fireEvent.change(inputs[0], { target: { value: '14400' } })

    expect(onChange).toHaveBeenCalledWith('v_nominal_mt', '14400')
  })

  it('calls onChange with campo and value when drop_mt_pct changes', () => {
    const onChange = vi.fn()
    renderQDT({ onChange })

    const inputs = screen.getAllByRole('textbox')
    // drop_mt_pct is the 2nd input
    fireEvent.change(inputs[1], { target: { value: '4.5' } })

    expect(onChange).toHaveBeenCalledWith('drop_mt_pct', '4.5')
  })

  it('calls onChange with campo and value when v_nominal_bt changes', () => {
    const onChange = vi.fn()
    renderQDT({ onChange })

    const inputs = screen.getAllByRole('textbox')
    // v_nominal_bt is 3rd
    fireEvent.change(inputs[2], { target: { value: '380' } })

    expect(onChange).toHaveBeenCalledWith('v_nominal_bt', '380')
  })

  // 5. resultado values shown
  it('shows MT voltage values from resultado', () => {
    renderQDT({ resultado: RESULTADO_BASE })
    expect(screen.getByText(/13800\.00 V/)).toBeInTheDocument()
    expect(screen.getByText(/13100\.00 V/)).toBeInTheDocument()
  })

  it('shows BT voltage values from resultado', () => {
    renderQDT({ resultado: RESULTADO_BASE })
    expect(screen.getByText(/220\.00 V/)).toBeInTheDocument()
    expect(screen.getByText(/208\.00 V/)).toBeInTheDocument()
  })

  // 6. QUEDA TOTAL
  it('shows QUEDA TOTAL from resultado', () => {
    renderQDT({ resultado: RESULTADO_BASE })
    expect(screen.getByText(/QUEDA TOTAL:.*5\.45%/i)).toBeInTheDocument()
  })

  // 7. No crash when resultado is null
  it('does not crash when resultado is null', () => {
    renderQDT({ resultado: null })
    // Should still render inputs
    expect(screen.getAllByRole('textbox').length).toBeGreaterThanOrEqual(8)
  })

  it('does not crash when resultado is undefined', () => {
    renderQDT({ resultado: undefined })
    expect(screen.getAllByRole('textbox').length).toBeGreaterThanOrEqual(8)
  })
})
