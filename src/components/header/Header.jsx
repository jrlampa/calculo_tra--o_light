// Header.jsx — Cabeçalho fiel ao Excel: Órgão | N.S. | Projeto | Ponto / Endereço / Estudado por | Matrícula | Data
import React from 'react'

/**
 * Campo de input estilo célula Excel com label alinhada à direita
 */
function Field({ label, id, value, onChange, width = 80, colSpan = 1 }) {
  return (
    <>
      <td 
        className="field-lbl" 
        style={{ 
          backgroundColor: '#E2E2E2', 
          border: '1px solid #999',
          textAlign: 'right',
          padding: '2px 4px',
          width: 80
        }}
      >
        {label}
      </td>
      <td 
        colSpan={colSpan}
        style={{ 
          border: '1px solid #999',
          padding: 0
        }}
      >
        <input
          id={id}
          className="xcell"
          style={{ 
            width: '100%', 
            border: 'none', 
            backgroundColor: '#fff',
            height: 18
          }}
          value={value ?? ''}
          onChange={e => onChange(id, e.target.value)}
        />
      </td>
    </>
  )
}

export default function Header({ dados, onChange }) {
  return (
    <table style={{ borderCollapse: 'collapse', marginBottom: 8, width: '100%', tableLayout: 'fixed' }}>
      <tbody>
        {/* Linha 1: Órgão | N.S. | Projeto | Ponto */}
        <tr style={{ height: 22 }}>
          <Field label="Órgão:"       id="orgao"    value={dados.orgao}   onChange={onChange} />
          <Field label="N.S.:"        id="ns"       value={dados.ns}      onChange={onChange} />
          <Field label="Projeto:"     id="projeto"  value={dados.projeto} onChange={onChange} />
          <Field label="Ponto:"       id="ponto"    value={dados.ponto}   onChange={onChange} />
        </tr>
        {/* Linha 2: Endereço | Matrícula | Data */}
        <tr style={{ height: 22 }}>
          <Field label="Endereço:"    id="endereco" value={dados.endereco} onChange={onChange} colSpan={3} />
          <Field label="Matrícula:"   id="matricula" value={dados.matricula} onChange={onChange} />
          <Field label="Data:"        id="data"      value={dados.data}      onChange={onChange} />
        </tr>
        {/* Linha 3: Estudado por */}
        <tr style={{ height: 22 }}>
          <Field label="Estudado por:" id="estudadoPor" value={dados.estudadoPor} onChange={onChange} colSpan={3} />
          <td colSpan={4} style={{ border: '1px solid #999', backgroundColor: '#f9f9f9' }} />
        </tr>
      </tbody>
    </table>
  )
}
