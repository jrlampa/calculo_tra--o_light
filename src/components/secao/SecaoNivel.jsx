// SecaoNivel.jsx — Seção genérica de nível de rede (MT1, MT2, BT, Ramais)
// Layout fiel ao Excel: label alinhado à esquerda, inputs cinza, unidade à direita
import React from 'react'

/** Largura fixa da coluna de labels (px) */
const LBL_W = 108

/**
 * @param {Object}   props
 * @param {string}   props.titulo         - Ex: "MT - 1º Nível"
 * @param {string}   props.labelResultado - Ex: "TRAÇÃO MT 1º NÍVEL (100 mm do topo):  daN °"
 * @param {Array}    props.travessias     - array[4] de objetos com campos
 * @param {Function} props.onChangeTravessia - callback(idx, campo, valor)
 * @param {Array}    props.campos         - [{campo, label, unidade}]
 * @param {string}   props.nota           - node opcional ex: "(*) - Considerar..."
 */
const SecaoNivel = ({ titulo, labelResultado, travessias, onChangeTravessia, campos, nota, config }) => {
  const buildAccessibleName = (fieldLabel, travessiaIndex) => (
    `${fieldLabel}, travessia ${travessiaIndex + 1}, ${titulo}`
  )

  return (
    <div className="sec-panel">
      {/* ── Título ─────────────────────────────────────── */}
      <div className="sec-title">{titulo}</div>

      {/* ── Tabela de dados ───────────────────────────── */}
      <table className="sec-table" style={{ tableLayout: 'fixed' }}>
        <colgroup>
          {/* coluna de labels */}
          <col style={{ width: LBL_W }} />
          {/* 4 travessias, cada uma com: input + unidade */}
          <col style={{ width: '22%' }} />
          <col style={{ width: 18 }} />
          <col style={{ width: '22%' }} />
          <col style={{ width: 18 }} />
          <col style={{ width: '22%' }} />
          <col style={{ width: 18 }} />
          <col style={{ width: '22%' }} />
          <col style={{ width: 18 }} />
        </colgroup>

        <thead>
          <tr>
            <th />
            {travessias.map((_, i) => (
              <th key={i} className="col-hdr" colSpan={2}>{`T${i + 1}`}</th>
            ))}
          </tr>
        </thead>

        <tbody>
          {campos.map(({ campo, label, unidade, isDropdown, configKey }) => (
            <tr key={campo}>
              {/* Label esquerda */}
              <td className="field-lbl">{label}</td>

              {/* 4 travessias */}
              {travessias.map((t, i) => {
                const isAlturaField = campo === 'alturaPoste' || campo === 'alturaAncoragem';
                const shouldHide = isAlturaField && i > 0;

                if (shouldHide) {
                  return (
                    <React.Fragment key={i}>
                      <td />
                      <td className="xunit" />
                    </React.Fragment>
                  );
                }

                return (
                  <React.Fragment key={i}>
                    <td>
                      {isDropdown ? (
                        <select
                          id={`${campo}-t${i + 1}`}
                          className="xcell"
                          style={{ width: "100%" }}
                          value={t[campo] ?? ""}
                          onChange={(e) => onChangeTravessia(i, campo, e.target.value)}
                          aria-label={buildAccessibleName(label, i)}
                        >
                          <option value="">...</option>
                          {(() => {
                            let options = config[configKey] || [];
                            // Filtro dinâmico Cabos -> Redes (Paridade Excel)
                            if (campo === "tipoCabo" && config.cabos_por_rede) {
                              const redeAtual = t.tipoRede;
                              if (redeAtual && config.cabos_por_rede[redeAtual]) {
                                options = config.cabos_por_rede[redeAtual];
                              }
                            }
                            return options.map((opt) => (
                              <option key={opt} value={opt}>
                                {opt}
                              </option>
                            ));
                          })()}
                        </select>
                      ) : (
                        <input
                          id={`${campo}-t${i + 1}`}
                          className="xcell"
                          style={{ width: '100%' }}
                          value={t[campo] ?? ''}
                          onChange={e => onChangeTravessia(i, campo, e.target.value)}
                          aria-label={buildAccessibleName(label, i)}
                          inputMode="decimal"
                        />
                      )}
                    </td>
                    <td className="xunit">{unidade}</td>
                  </React.Fragment>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>

      {/* ── Rodapé: resultado + nota ──────────────────── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span className="res-lbl">{labelResultado}</span>
        {nota && (
          <span style={{ fontSize: 9, color: '#444', marginRight: 8, textAlign: 'right', lineHeight: 1.4 }}>
            {nota}
          </span>
        )}
      </div>
    </div>
  )
}

// Memoização com comparação customizada para evitar re-renders desnecessários
export default React.memo(SecaoNivel, (prevProps, nextProps) => {
  // Comparar apenas as props que realmente afetam o render
  return (
    prevProps.titulo === nextProps.titulo &&
    prevProps.labelResultado === nextProps.labelResultado &&
    prevProps.travessias === nextProps.travessias &&
    prevProps.onChangeTravessia === nextProps.onChangeTravessia &&
    prevProps.campos === nextProps.campos &&
    prevProps.nota === nextProps.nota &&
    prevProps.config === nextProps.config
  )
})
