/**
 * The SecaoQDT function in JavaScript React renders a section for calculating voltage drop percentage
 * with input fields and displays the calculated results.
 */
import React from 'react'

export default function SecaoQDT({ dados, onChange, resultado }) {
  const handleChange = (campo, valor) => {
    onChange(campo, valor)
  }

  return (
    <div className="sec-panel">
      <div className="sec-title">Queda de Tensão (QDT) %</div>
      
      <table className="sec-table sec-table--qdt">
        <colgroup>
          <col className="col-qdt-lbl" />
          <col className="col-qdt-in" />
          <col className="col-qdt-unit" />
          <col className="col-qdt-lbl" />
          <col className="col-qdt-in" />
          <col className="col-qdt-unit" />
        </colgroup>
        <tbody>
          <tr>
            <td className="xlbl">V Nominal MT:</td>
            <td>
              <input 
                className="xcell w-full" 
                value={dados.v_nominal_mt} 
                onChange={e => handleChange('v_nominal_mt', e.target.value)} 
              />
            </td>
            <td className="xunit">V</td>
            <td className="xlbl">Queda MT (%):</td>
            <td>
              <input 
                className="xcell w-full" 
                value={dados.drop_mt_pct} 
                onChange={e => handleChange('drop_mt_pct', e.target.value)} 
              />
            </td>
            <td className="xunit">%</td>
          </tr>
          <tr>
            <td className="xlbl">V Nominal BT:</td>
            <td>
              <input 
                className="xcell w-full" 
                value={dados.v_nominal_bt} 
                onChange={e => handleChange('v_nominal_bt', e.target.value)} 
              />
            </td>
            <td className="xunit">V</td>
            <td className="xlbl">Queda Trafo (%):</td>
            <td>
              <input 
                className="xcell w-full" 
                value={dados.drop_trafo_pct} 
                onChange={e => handleChange('drop_trafo_pct', e.target.value)} 
              />
            </td>
            <td className="xunit">%</td>
          </tr>
          <tr>
            <td className="xlbl">Coef. Perda:</td>
            <td>
              <input 
                className="xcell w-full" 
                value={dados.coef_perda} 
                onChange={e => handleChange('coef_perda', e.target.value)} 
              />
            </td>
            <td className="xunit"></td>
            <td className="xlbl">Queda BT1 (%):</td>
            <td>
              <input 
                className="xcell w-full" 
                value={dados.drop_bt1_pct} 
                onChange={e => handleChange('drop_bt1_pct', e.target.value)} 
              />
            </td>
            <td className="xunit">%</td>
          </tr>
          <tr>
            <td className="xlbl">Regulagem MT:</td>
            <td>
              <input 
                className="xcell w-full" 
                value={dados.reg_mt} 
                onChange={e => handleChange('reg_mt', e.target.value)} 
              />
            </td>
            <td className="xunit"></td>
            <td className="xlbl">Queda BT2 (%):</td>
            <td>
              <input 
                className="xcell w-full" 
                value={dados.drop_bt2_pct} 
                onChange={e => handleChange('drop_bt2_pct', e.target.value)} 
              />
            </td>
            <td className="xunit">%</td>
          </tr>
        </tbody>
      </table>

      <div className="qdt-results">
        <div className="qdt-results-grid">
          <div>
            <strong>MT Inicial:</strong> {resultado?.v_mt_initial?.toFixed(2)} V<br/>
            <strong>MT resultante:</strong> {resultado?.v_mt_node?.toFixed(2)} V
          </div>
          <div>
            <strong>BT Início:</strong> {resultado?.v_bt_start?.toFixed(2)} V<br/>
            <strong>BT Final:</strong> {resultado?.v_bt_node2?.toFixed(2)} V
          </div>
        </div>
        <div className="res-lbl">
          QUEDA TOTAL: {resultado?.drop_total_pct?.toFixed(2)}%
        </div>
      </div>
    </div>
  )
}
