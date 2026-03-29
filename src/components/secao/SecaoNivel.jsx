/* This code defines a React component called `SecaoNivel`, which represents a generic section for
network level (MT1, MT2, BT, Ramais). The component renders a section with a title, a table of data
with multiple rows and columns, and a footer displaying a result label and an optional note. */
// SecaoNivel.jsx — Seção genérica de nível de rede (MT1, MT2, BT, Ramais)
// Layout fiel ao Excel: label alinhado à esquerda, inputs cinza, unidade à direita
import React from 'react'

/**
 * @param {Object}   props
 * @param {string}   props.titulo         - Ex: "MT - 1º Nível"
 * @param {string}   props.labelResultado - Ex: "TRAÇÃO MT 1º NÍVEL (100 mm do topo):  daN °"
 * @param {Array}    props.travessias     - array[4] de objetos com campos
 * @param {Function} props.onChangeTravessia - callback(idx, campo, valor)
 * @param {Array}    props.campos         - [{campo, label, unidade}]
 * @param {string}   props.nota           - node opcional ex: "(*) - Considerar..."
 * @param {string}   props.sectionError   - mensagem de erro 422 de validação para esta seção (opcional)
 */
const SecaoNivel = ({ titulo, labelResultado, travessias, onChangeTravessia, campos, nota, config, sectionError }) => {
  const buildAccessibleName = (fieldLabel, travessiaIndex) => (
    `${fieldLabel}, travessia ${travessiaIndex + 1}, ${titulo}`
  )

  return (
    <div className="sec-panel">
      {/* ── Título ─────────────────────────────────────── */}
      <div className="sec-title">{titulo}</div>

      {/* ── Tabela de dados ───────────────────────────── */}
      <table className="sec-table">
        <colgroup>
          {/* coluna de labels */}
          <col className="col-lbl" />
          {/* 4 travessias, cada uma com: input + unidade */}
          <col className="col-input" />
          <col className="col-unit" />
          <col className="col-input" />
          <col className="col-unit" />
          <col className="col-input" />
          <col className="col-unit" />
          <col className="col-input" />
          <col className="col-unit" />
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
      <div className="sec-footer">
        <span className="res-lbl">{labelResultado}</span>
        {nota && (
          <span className="sec-note">
            {nota}
          </span>
        )}
        {sectionError && (
          <p className="sec-field-error" role="alert" aria-live="polite">
            {sectionError}
          </p>
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
    prevProps.config === nextProps.config &&
    prevProps.sectionError === nextProps.sectionError
  )
})
