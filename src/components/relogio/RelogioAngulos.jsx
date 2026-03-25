/**
 * The `RelogioAngulos` function in JavaScript React creates a clock-like visualization of traction
 * angles with vectors and a resultant vector, along with a textual summary of the vectors and
 * resultant.
 * @returns The `RelogioAngulos` component is being returned. It consists of a canvas element that
 * displays a clock-like visualization of angles and vectors, along with a summary text below the
 * canvas. The canvas renders ticks, labels, reference lines, traction vectors, and a resultant vector
 * based on the provided input props (`vetores`, `resultante`, `resumoDados`). The summary text
 * provides information
 */
// RelogioAngulos.jsx — Relógio de ângulos idêntico ao Excel
// Linhas vermelhas = vetores de tração; linha grossa vermelha = resultante
import React, { useEffect, useMemo, useRef } from 'react'

const SIZE = 260
const CX   = SIZE / 2
const CY   = SIZE / 2
const R    = 95   // raio da linha de ticks
const RL   = 113  // raio dos labels

// Ticks conforme a imagem do Excel (sentido anti-horário a partir da direita)
const TICKS = [
  { deg: 90,  label: '90°'  },
  { deg: 105, label: '105°' },
  { deg: 120, label: '120°' },
  { deg: 135, label: '135°' },
  { deg: 140, label: '140°' },
  { deg: 150, label: '150°' },
  { deg: 165, label: '165°' },
  { deg: 180, label: '180°' },
  { deg: 195, label: '195°' },
  { deg: 210, label: '210°' },
  { deg: 225, label: '225°' },
  { deg: 255, label: '255°' },
  { deg: 270, label: '270°' },
  { deg: 285, label: '285°' },
  { deg: 300, label: '300°' },
  { deg: 315, label: '315°' },
  { deg: 330, label: '330°' },
  { deg: 345, label: '345°' },
  { deg: 0,   label: '0°\n360°' },  // duplo label no Excel
  { deg: 15,  label: '15°'  },
  { deg: 30,  label: '30°'  },
  { deg: 45,  label: '45°'  },
  { deg: 60,  label: '60°'  },
  { deg: 75,  label: '75°'  },
]

// Converte grau cartográfico (0°=leste, anti-horário) para radianos canvas
function toRad(deg) {
  return (-deg * Math.PI) / 180
}

function polar(deg, r) {
  const a = toRad(deg)
  return { x: CX + r * Math.cos(a), y: CY + r * Math.sin(a) }
}

function formatPt(value, digits = 1) {
  if (typeof value !== 'number' || Number.isNaN(value)) return null
  return value.toLocaleString('pt-BR', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

/**
 * @param {Array}  vetores      [{angulo, magnitude}] — vetores de tração (linhas vermelhas finas)
 * @param {Object} resultante   {angulo, magnitude}   — resultante (linha vermelha grossa)
 * @param {Object} resumoDados  payload de resultado completo para resumo textual equivalente
 */
export default function RelogioAngulos({ vetores = [], resultante = null, resumoDados = null }) {
  const ref = useRef(null)

  const resumoTexto = useMemo(() => {
    const totalTracao = typeof resumoDados?.total_tracao_dan === 'number'
      ? resumoDados.total_tracao_dan
      : null
    const totalAngulo = typeof resumoDados?.total_angulo_graus === 'number'
      ? resumoDados.total_angulo_graus
      : (typeof resultante?.angulo === 'number' ? resultante.angulo : null)

    const vetoresResumo = Array.isArray(resumoDados?.vetores)
      ? resumoDados.vetores
      : []

    const principaisVetores = [...vetoresResumo]
      .filter(v => typeof v?.tracao_dan === 'number' && typeof v?.angulo_graus === 'number')
      .sort((a, b) => b.tracao_dan - a.tracao_dan)
      .slice(0, 3)

    const resultanteTexto = (() => {
      const angulo = formatPt(totalAngulo ?? 0, 1)
      if (totalTracao === null) {
        return `Resultante em ${angulo}°.`
      }

      const tracao = formatPt(totalTracao, 1)
      return `Resultante em ${angulo}° com ${tracao} daN.`
    })()

    if (principaisVetores.length === 0) {
      return `${resultanteTexto} Sem vetores auxiliares relevantes no momento.`
    }

    const vetoresTexto = principaisVetores
      .map(v => {
        const tracao = formatPt(v.tracao_dan, 1)
        const angulo = formatPt(v.angulo_graus, 1)
        return `${v.label || 'Vetor'} (${tracao} daN, ${angulo}°)`
      })
      .join('; ')

    return `${resultanteTexto} Principais vetores: ${vetoresTexto}.`
  }, [resumoDados, resultante?.angulo])

  useEffect(() => {
    const canvas = ref.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')

    ctx.clearRect(0, 0, SIZE, SIZE)

    // ── Eixos cruzados (linhas de referência 0°/180° e 90°/270°) ──
    ;[[0, 180], [90, 270]].forEach(([a, b]) => {
      const pa = polar(a, R)
      const pb = polar(b, R)
      ctx.beginPath()
      ctx.strokeStyle = '#aaa'
      ctx.lineWidth = 0.7
      ctx.setLineDash([4, 4])
      ctx.moveTo(pa.x, pa.y)
      ctx.lineTo(pb.x, pb.y)
      ctx.stroke()
    })
    ctx.setLineDash([])

    // ── Ticks e labels ─────────────────────────────────────────────
    TICKS.forEach(({ deg, label }) => {
      const inner = polar(deg, R - 5)
      const outer = polar(deg, R + 5)
      ctx.beginPath()
      ctx.strokeStyle = '#555'
      ctx.lineWidth = 0.8
      ctx.moveTo(inner.x, inner.y)
      ctx.lineTo(outer.x, outer.y)
      ctx.stroke()

      // Label
      const lp = polar(deg, RL)
      const lines = label.split('\n')
      ctx.fillStyle = '#333'
      ctx.font = '7.5px Calibri,Arial'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      lines.forEach((ln, i) => {
        ctx.fillText(ln, lp.x, lp.y + (i - (lines.length - 1) / 2) * 9)
      })
    })

    // ── Linhas de referência diagonais ──────────────────────────
    const diags = [45, 135, 225, 315]
    diags.forEach(deg => {
      const pa = polar(deg, R)
      const pb = polar(deg + 180, R)
      ctx.beginPath()
      ctx.strokeStyle = '#ccc'
      ctx.lineWidth = 0.5
      ctx.moveTo(pa.x, pa.y)
      ctx.lineTo(pb.x, pb.y)
      ctx.stroke()
    })

    // ── Vetores de tração (vermelho negritado) ───────────────────
    vetores.forEach(({ angulo, magnitude = 1 }) => {
      const end = polar(angulo, (R - 5) * magnitude)
      ctx.beginPath()
      ctx.strokeStyle = '#C00000'
      ctx.lineWidth = 2.2
      ctx.moveTo(CX, CY)
      ctx.lineTo(end.x, end.y)
      ctx.stroke()
      // seta
      const rad = toRad(angulo)
      const as = 6
      ctx.beginPath()
      ctx.fillStyle = '#C00000'
      ctx.moveTo(end.x, end.y)
      ctx.lineTo(end.x - as * Math.cos(rad - 0.45), end.y - as * Math.sin(rad - 0.45))
      ctx.lineTo(end.x - as * Math.cos(rad + 0.45), end.y - as * Math.sin(rad + 0.45))
      ctx.closePath()
      ctx.fill()
    })

    // ── Resultante (vermelho super grosso e longo) ───────────────
    if (resultante && resultante.magnitude > 0) {
      // Faz a resultante um pouco mais longa para destaque total
      const end = polar(resultante.angulo, (R - 2) * (resultante.magnitude ?? 1))
      ctx.beginPath()
      ctx.strokeStyle = '#C00000'
      ctx.lineWidth = 4.8
      ctx.moveTo(CX, CY)
      ctx.lineTo(end.x, end.y)
      ctx.stroke()
      const rad = toRad(resultante.angulo)
      const as = 9
      ctx.beginPath()
      ctx.fillStyle = '#C00000'
      ctx.moveTo(end.x, end.y)
      ctx.lineTo(end.x - as * Math.cos(rad - 0.35), end.y - as * Math.sin(rad - 0.35))
      ctx.lineTo(end.x - as * Math.cos(rad + 0.35), end.y - as * Math.sin(rad + 0.35))
      ctx.closePath()
      ctx.fill()
    }

    // ── Ponto central ────────────────────────────────────────────
    ctx.beginPath()
    ctx.arc(CX, CY, 3, 0, 2 * Math.PI)
    ctx.fillStyle = '#333'
    ctx.fill()
  }, [vetores, resultante])

  return (
    <div className="grafico-wrapper">
      <canvas
        ref={ref}
        width={SIZE}
        height={SIZE}
        aria-label="Relógio de ângulos de tração"
        style={{ display: 'block' }}
      />
      <p className="grafico-summary" role="note">
        {resumoTexto}
      </p>
    </div>
  )
}
