// TabelaCarga.jsx — Tabela R (daN) vs α vs Carga Nominal do poste
import React from 'react'

/**
 * @param {Object} props
 * @param {Array}  props.dados - tabelaCargas do mockData
 */
export default function TabelaCarga({ dados }) {
  return (
    <div className="mt-2">
      <table className="border-collapse text-[8px]" style={{ borderColor: '#999' }}>
        <thead>
          <tr className="bg-gray-200">
            <th className="border border-gray-400 px-1 py-0 text-center font-bold" rowSpan={2}>α °</th>
            <th className="border border-gray-400 px-1 py-0 text-center font-bold" colSpan={2}>R (daN)</th>
          </tr>
          <tr className="bg-gray-100">
            <th className="border border-gray-400 px-1 py-0 text-center font-bold" colSpan={2}>
              Carga Nominal do poste (daN)
            </th>
          </tr>
          <tr className="bg-gray-100">
            <th className="border border-gray-400 px-1 py-0 w-6" />
            <th className="border border-gray-400 px-1 py-0 text-center text-[7px]">300</th>
            <th className="border border-gray-400 px-1 py-0 text-center text-[7px]">600</th>
          </tr>
        </thead>
        <tbody>
          {dados.map((row, i) => (
            <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="border border-gray-400 px-1 text-center">{row.alpha}</td>
              <td className="border border-gray-400 px-1 text-center">{row.R300}</td>
              <td className="border border-gray-400 px-1 text-center">{row.R600}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
