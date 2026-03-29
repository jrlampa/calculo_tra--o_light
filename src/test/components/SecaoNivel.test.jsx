/**
 * Tests for SecaoNivel component.
 *
 * Covered paths:
 *  1. Renders section title.
 *  2. Renders four traversal header columns (T1–T4).
 *  3. Renders text inputs for numeric fields.
 *  4. Renders dropdown selects for fields with isDropdown=true.
 *  5. Dropdown select includes options from config.
 *  6. Altura fields (alturaPoste / alturaAncoragem) only show one input (T1 merged).
 *  7. onChangeTravessia called with correct args when text input changes.
 *  8. onChangeTravessia called with correct args when select changes.
 *  9. Footer displays labelResultado.
 * 10. Nota text rendered when provided.
 * 11. sectionError displayed with role=alert when provided.
 * 12. sectionError not rendered when absent.
 * 13. Dropdown tipoCabo filters by cabos_por_rede when tipoRede is set.
 */
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'

import SecaoNivel from '@/components/secao/SecaoNivel'

// ─── helpers ──────────────────────────────────────────────────────────────────

const CAMPOS_MT = [
  { campo: 'tipoRede', label: 'Tipo de rede', unidade: '', isDropdown: true, configKey: 'redes' },
  { campo: 'tipoCabo', label: 'Tipo de cabo', unidade: '', isDropdown: true, configKey: 'cabos' },
  { campo: 'vao', label: 'Vão', unidade: 'm' },
  { campo: 'flecha', label: 'Flecha', unidade: 'm' },
  { campo: 'alturaPoste', label: 'Altura poste', unidade: 'm' },
  { campo: 'alturaAncoragem', label: 'Altura ancoragem', unidade: 'm' },
]

const CONFIG = {
  redes: ['Convencional', 'Compacta'],
  cabos: ['CAA', 'AACSR'],
  cabos_por_rede: {
    Convencional: ['CAA', 'AACSR'],
    Compacta: ['CU'],
  },
}

function makeTravessias(overrides = {}) {
  return [0, 1, 2, 3].map(() => ({
    tipoRede: '',
    tipoCabo: '',
    vao: '',
    flecha: '',
    alturaPoste: '11',
    alturaAncoragem: '9.2',
    ...overrides,
  }))
}

function renderSecao(props = {}) {
  return render(
    <SecaoNivel
      titulo="MT - 1º Nível"
      labelResultado="TRAÇÃO MT 1º NÍVEL: 0 daN"
      travessias={makeTravessias()}
      onChangeTravessia={vi.fn()}
      campos={CAMPOS_MT}
      config={CONFIG}
      {...props}
    />
  )
}

// ─── tests ────────────────────────────────────────────────────────────────────

describe('SecaoNivel', () => {
  // 1. Title
  it('renders the section title', () => {
    renderSecao()
    expect(screen.getByText('MT - 1º Nível')).toBeInTheDocument()
  })

  // 2. Traversal headers T1–T4
  it('renders four traversal headers T1 through T4', () => {
    renderSecao()
    expect(screen.getByText('T1')).toBeInTheDocument()
    expect(screen.getByText('T2')).toBeInTheDocument()
    expect(screen.getByText('T3')).toBeInTheDocument()
    expect(screen.getByText('T4')).toBeInTheDocument()
  })

  // 3. Text inputs for numeric fields
  it('renders numeric text inputs for non-dropdown fields', () => {
    renderSecao()
    // "Vão" — 4 inputs, one per traversal
    const vaoInputs = screen.getAllByLabelText(/vão, travessia \d+, MT - 1º Nível/i)
    expect(vaoInputs.length).toBe(4)
    expect(vaoInputs[0].tagName).toBe('INPUT')
  })

  // 4. Dropdown selects
  it('renders dropdown selects for isDropdown=true fields', () => {
    renderSecao()
    const tipoRedeSelects = screen.getAllByLabelText(/tipo de rede, travessia \d+/i)
    expect(tipoRedeSelects.length).toBe(4)
    expect(tipoRedeSelects[0].tagName).toBe('SELECT')
  })

  // 5. Dropdown options from config
  it('dropdown options include config values', () => {
    renderSecao()
    const firstSelect = screen.getAllByLabelText(/tipo de rede, travessia 1/i)[0]
    expect(firstSelect).toHaveTextContent('Convencional')
    expect(firstSelect).toHaveTextContent('Compacta')
  })

  // 6. Altura fields — only T1 has an input, T2-T4 are hidden cells
  it('alturaPoste field only renders input for T1 (merged cell behavior)', () => {
    renderSecao()
    const alturaInputs = screen.getAllByLabelText(/altura poste, travessia \d+/i)
    // Only T1 is interactive
    expect(alturaInputs.length).toBe(1)
  })

  // 7. onChangeTravessia called with text input change
  it('calls onChangeTravessia(idx, campo, value) when text input changes', () => {
    const onChangeTravessia = vi.fn()
    renderSecao({ onChangeTravessia })

    const vaoInput = screen.getAllByLabelText(/vão, travessia 1/i)[0]
    fireEvent.change(vaoInput, { target: { value: '42.5' } })

    expect(onChangeTravessia).toHaveBeenCalledWith(0, 'vao', '42.5')
  })

  it('calls onChangeTravessia with correct traversal index for T3', () => {
    const onChangeTravessia = vi.fn()
    renderSecao({ onChangeTravessia })

    const vaoInputT3 = screen.getAllByLabelText(/vão, travessia 3/i)[0]
    fireEvent.change(vaoInputT3, { target: { value: '30' } })

    expect(onChangeTravessia).toHaveBeenCalledWith(2, 'vao', '30')
  })

  // 8. onChangeTravessia called via select
  it('calls onChangeTravessia when select value changes', () => {
    const onChangeTravessia = vi.fn()
    renderSecao({ onChangeTravessia })

    const tipoRedeSelect = screen.getAllByLabelText(/tipo de rede, travessia 1/i)[0]
    fireEvent.change(tipoRedeSelect, { target: { value: 'Convencional' } })

    expect(onChangeTravessia).toHaveBeenCalledWith(0, 'tipoRede', 'Convencional')
  })

  // 9. Footer result label
  it('renders labelResultado in the footer', () => {
    renderSecao()
    expect(screen.getByText(/TRAÇÃO MT 1º NÍVEL: 0 daN/i)).toBeInTheDocument()
  })

  // 10. Nota text
  it('renders nota when provided', () => {
    renderSecao({ nota: '(*) Considerar 10% de acréscimo.' })
    expect(screen.getByText(/Considerar 10%/)).toBeInTheDocument()
  })

  it('does not render nota when absent', () => {
    renderSecao()
    expect(screen.queryByText(/Considerar/)).not.toBeInTheDocument()
  })

  // 11. sectionError
  it('renders sectionError with role=alert', () => {
    renderSecao({ sectionError: 'Vão inválido para esta seção.' })
    const alert = screen.getByRole('alert')
    expect(alert).toBeInTheDocument()
    expect(alert).toHaveTextContent(/Vão inválido/)
  })

  // 12. No error when sectionError absent
  it('does not render alert when sectionError is absent', () => {
    renderSecao()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  // 13. tipoCabo filtered by cabos_por_rede
  it('filters tipoCabo options by tipoRede when cabos_por_rede is configured', () => {
    const travessiasComRede = makeTravessias({ tipoRede: 'Compacta' })
    renderSecao({ travessias: travessiasComRede })

    const tipoCaboSelects = screen.getAllByLabelText(/tipo de cabo, travessia 1/i)
    expect(tipoCaboSelects.length).toBe(1)
    // Only "CU" from Compacta network
    expect(tipoCaboSelects[0]).toHaveTextContent('CU')
    expect(tipoCaboSelects[0]).not.toHaveTextContent('CAA')
  })
})
