/**
 * The function `TabelaCarga` renders a table component in React to display data related to loads and
 * angles.
 * @returns The `TabelaCarga` component is being returned. It is a functional component that renders a
 * table based on the provided `dados` prop. The table structure includes headers for angles (α °) and
 * forces (R) at 300 and 600 daN, and it maps through the `dados` array to display the corresponding
 * data rows.
 */
import React from 'react'

export default function TabelaCarga({ dados }) {
  return (
    <div className="mt-2 mb-20 sm:mb-0 md:mb-0 overflow-x-auto md:overflow-visible">
      <table 
        className="border-collapse text-[8px] md:text-[9px] w-full md:w-auto border-[#999]"
      >
        <thead>
          <tr className="bg-gray-200">
            <th className="border border-gray-400 px-0.5 md:px-1 py-0 text-center font-bold" rowSpan={2}>
              α °
            </th>
            <th className="border border-gray-400 px-0.5 md:px-1 py-0 text-center font-bold" colSpan={2}>
              R (daN)
            </th>
          </tr>
          <tr className="bg-gray-100">
            <th className="border border-gray-400 px-0.5 md:px-1 py-0 text-center font-bold whitespace-nowrap" colSpan={2}>
              Esforços (daN)
            </th>
          </tr>
          <tr className="bg-gray-100">
            <th className="border border-gray-400 px-0.5 md:px-1 py-0 w-4 md:w-6" />
            <th className="border border-gray-400 px-0.5 md:px-1 py-0 text-center text-[7px]">
              300
            </th>
            <th className="border border-gray-400 px-0.5 md:px-1 py-0 text-center text-[7px]">
              600
            </th>
          </tr>
        </thead>
        <tbody>
          {dados.map((row, i) => (
            <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="border border-gray-400 px-0.5 md:px-1 py-0 text-center font-mono">
                {row.alpha}
              </td>
              <td className="border border-gray-400 px-0.5 md:px-1 py-0 text-center font-mono whitespace-nowrap">
                {row.R300}
              </td>
              <td className="border border-gray-400 px-0.5 md:px-1 py-0 text-center font-mono whitespace-nowrap">
                {row.R600}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
