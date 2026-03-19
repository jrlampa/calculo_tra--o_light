// Header.jsx — Cabeçalho fiel ao Excel: Órgão | N.S. | Projeto | Ponto / Endereço / Estudado por | Matrícula | Data
import React from 'react'

/**
 * Campo de input estilo célula Excel com label alinhada à direita
 */
function Field({ label, id, value, onChange, width = 80, labelWidth = 'auto' }) {
  return (
    <>
      <td className="xlbl" style={{ width: labelWidth !== 'auto' ? labelWidth : undefined }}>
        {label}
      </td>
      <td style={{ paddingRight: 8 }}>
        <input
          id={id}
          className="xcell"
          style={{ width }}
          value={value ?? ''}
          onChange={e => onChange(id, e.target.value)}
        />
      </td>
    </>
  )
}

export default function Header({ dados, onChange }) {
  return (
    <table style={{ borderCollapse: 'collapse', marginBottom: 4, width: '100%' }}>
      <tbody>
        {/* Linha 1: Órgão | N.S. | Projeto | Ponto */}
        <tr>
          <Field label="Órgão:"       id="orgao"    value={dados.orgao}   onChange={onChange} width={90}  />
          <Field label="N.S.:"        id="ns"       value={dados.ns}      onChange={onChange} width={70}  />
          <Field label="Projeto:"     id="projeto"  value={dados.projeto} onChange={onChange} width={160} />
          <Field label="Ponto:"       id="ponto"    value={dados.ponto}   onChange={onChange} width={80}  />
        </tr>
        {/* Linha 2: Endereço */}
        <tr>
          <Field label="Endereço:"    id="endereco" value={dados.endereco}     onChange={onChange} width={320} />
          <td colSpan={6} />
        </tr>
        {/* Linha 3: Estudado por | Matrícula | Data */}
        <tr>
          <Field label="Estudado por:" id="estudadoPor" value={dados.estudadoPor} onChange={onChange} width={110} />
          <Field label="Matrícula:"    id="matricula"   value={dados.matricula}   onChange={onChange} width={80}  />
          <Field label="Data:"         id="data"        value={dados.data}        onChange={onChange} width={90}  />
          <td colSpan={2} />
        </tr>
      </tbody>
    </table>
  )
}
