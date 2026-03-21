# Relatório Técnico - UX/UI Designer

## 📊 Análise de Experiência do Usuário

### Estado Atual da UI/UX
- **Design System**: Tailwind CSS (✅ presente)
- **Componentes**: 9 componentes implementados
- **Responsive**: Implementado (desktop/tablet/mobile)
- **Accessibility**: WCAG 2.1 AA parcial (✅ implementado)
- **Visual**: Herança do Excel (limitada)

### 🏗️ Arquitetura de UI

```
Componentes Atuais:
├── Header.jsx (status indicators)
├── FlowStepper.jsx (navegação)
├── RelogioAngulos.jsx (diagrama)
├── DiagramaPoste.jsx (visualização)
├── TabelaCarga.jsx (dados)
├── MobileActionBar.jsx (ações)
├── TelaProjetoInicial.jsx (onboarding)
└── SecaoNivel.jsx (formulários)

Design System:
├── Tailwind CSS (utility-first)
├── Safe area utilities
├── Responsive breakpoints
└── Color system (limitado)
```

## ⚠️ Problemas Críticos Identificados

### 🚨 Crítico (Impacto Alto/Esf. Baixo)

#### 1. **Design System Inexistente**
```css
/* PROBLEMA: Sem design system unificado */
/* Cores hardcoded */
.bg-blue-600 { background-color: rgb(37 99 235); }
/* Sem tokens semânticos */
/* Sem consistência visual */
/* Sem guia de uso */
```

**Solução Imediata**: Design System Completo
```css
/* design-system/tokens.css */
:root {
  /* Cores Primárias */
  --color-primary-50: #eff6ff;
  --color-primary-500: #3b82f6;
  --color-primary-600: #2563eb;
  --color-primary-700: #1d4ed8;
  
  /* Cores Semânticas */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-info: #6366f1;
  
  /* Neutral Scale */
  --color-gray-50: #f9fafb;
  --color-gray-900: #111827;
  
  /* Tipografia */
  --font-size-xs: 0.75rem;    /* 12px */
  --font-size-sm: 0.875rem;   /* 14px */
  --font-size-base: 1rem;     /* 16px */
  --font-size-lg: 1.125rem;   /* 18px */
  --font-size-xl: 1.25rem;    /* 20px */
  
  /* Espaçamento */
  --spacing-1: 0.25rem;   /* 4px */
  --spacing-2: 0.5rem;    /* 8px */
  --spacing-4: 1rem;      /* 16px */
  --spacing-8: 2rem;      /* 32px */
  
  /* Border Radius */
  --radius-sm: 0.125rem;  /* 2px */
  --radius-md: 0.375rem;  /* 6px */
  --radius-lg: 0.5rem;    /* 8px */
  
  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
}

/* design-system/components.css */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  font-weight: 500;
  transition: all 0.2s ease;
  cursor: pointer;
  border: 1px solid transparent;
}

.btn--primary {
  background-color: var(--color-primary-600);
  color: white;
  border-color: var(--color-primary-600);
}

.btn--primary:hover {
  background-color: var(--color-primary-700);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn--secondary {
  background-color: transparent;
  color: var(--color-primary-600);
  border-color: var(--color-primary-600);
}

.input {
  width: 100%;
  padding: var(--spacing-3) var(--spacing-4);
  border: 1px solid var(--color-gray-300);
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.input:focus {
  outline: none;
  border-color: var(--color-primary-500);
  box-shadow: 0 0 0 3px rgb(59 130 246 / 0.1);
}
```

#### 2. **Feedback Visual Insuficiente**
```jsx
// PROBLEMA: Sem micro-interactions
// Estados não claros
// Loading states inconsistentes
// Sem feedback de erro amigável
```

**Solução**: Sistema de Feedback Rico
```jsx
// components/Feedback/Toast.jsx
import React, { useEffect } from 'react'
import { CheckCircle, AlertCircle, XCircle, Info, X } from 'lucide-react'

const Toast = ({ type, message, onClose, duration = 5000 }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, duration)
    return () => clearTimeout(timer)
  }, [onClose, duration])

  const icons = {
    success: <CheckCircle className="w-5 h-5 text-green-500" />,
    error: <XCircle className="w-5 h-5 text-red-500" />,
    warning: <AlertCircle className="w-5 h-5 text-yellow-500" />,
    info: <Info className="w-5 h-5 text-blue-500" />
  }

  return (
    <div className="animate-slide-in-right">
      <div className="flex items-center p-4 bg-white rounded-lg shadow-lg border-l-4 border-l-{type === 'success' ? 'green' : type === 'error' ? 'red' : type === 'warning' ? 'yellow' : 'blue'}-500">
        {icons[type]}
        <p className="ml-3 text-sm font-medium text-gray-900">{message}</p>
        <button onClick={onClose} className="ml-auto text-gray-400 hover:text-gray-600">
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

// components/Feedback/LoadingSpinner.jsx
export const LoadingSpinner = ({ size = 'md', className = '' }) => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8'
  }

  return (
    <div className={`animate-spin ${sizes[size]} ${className}`}>
      <svg className="w-full h-full text-current" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
      </svg>
    </div>
  )
}

// components/Feedback/Skeleton.jsx
export const Skeleton = ({ className = '', height = 'h-4' }) => (
  <div className={`animate-pulse bg-gray-200 rounded ${height} ${className}`} />
)
```

#### 3. **Onboarding Inexistente**
```jsx
// PROBLEMA: Usuário perdido sem orientação
// Sem tutorial ou help
// Complexidade não explicada
```

**Solução**: Onboarding Estruturado
```jsx
// components/Onboarding/Tour.jsx
import React, { useState } from 'react'
import { ChevronRight, X, Skip } from 'lucide-react'

const TourStep = ({ step, onNext, onSkip, onClose }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-xl shadow-2xl max-w-md mx-4 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">{step.title}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="mb-6">
          {step.content}
        </div>
        
        <div className="flex items-center justify-between">
          <button onClick={onSkip} className="text-sm text-gray-500 hover:text-gray-700">
            Pular tour
          </button>
          <button 
            onClick={onNext}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            {step.isLast ? 'Começar' : 'Próximo'}
            <ChevronRight className="w-4 h-4 ml-1" />
          </button>
        </div>
        
        <div className="flex justify-center mt-4 space-x-1">
          {[...Array(step.total)].map((_, i) => (
            <div 
              key={i}
              className={`w-2 h-2 rounded-full ${
                i === step.current - 1 ? 'bg-blue-600' : 'bg-gray-300'
              }`}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

// Tour data
const tourSteps = [
  {
    title: 'Bem-vindo ao Cálculo de Tração!',
    content: (
      <div>
        <p className="text-gray-600 mb-4">
          Vamos te guiar pelos principais recursos para calcular a tração em postes de rede elétrica.
        </p>
        <div className="bg-blue-50 p-4 rounded-lg">
          <p className="text-sm text-blue-800">
            💡 Dica: Você pode acessar este tour novamente a qualquer momento pelo menu Ajuda.
          </p>
        </div>
      </div>
    ),
    current: 1,
    total: 5,
    isLast: false
  },
  {
    title: '1. Informe o Projeto',
    content: (
      <div>
        <p className="text-gray-600 mb-4">
          Comece cadastrando as informações do projeto: órgão, número, localização e responsável técnico.
        </p>
        <div className="bg-gray-100 p-3 rounded-lg">
          <p className="text-sm font-mono">Ex: COELBA • NS: 123456 • Salvador-BA</p>
        </div>
      </div>
    ),
    current: 2,
    total: 5,
    isLast: false
  },
  {
    title: '2. Defina o Ponto',
    content: (
      <div>
        <p className="text-gray-600 mb-4">
          Para cada poste, informe a identificação e selecione o tipo/modelo adequado.
        </p>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="bg-gray-100 p-2 rounded">Identificação: P-001</div>
          <div className="bg-gray-100 p-2 rounded">Poste: Concreto 12-300</div>
        </div>
      </div>
    ),
    current: 3,
    total: 5,
    isLast: false
  },
  {
    title: '3. Configure as Travessias',
    content: (
      <div>
        <p className="text-gray-600 mb-4">
          Informe os dados de cada nível: MT, BT, BTZ e Ramais. O sistema calculará automaticamente as trações.
        </p>
        <div className="bg-yellow-50 p-3 rounded-lg">
          <p className="text-sm text-yellow-800">
            ⚠️ Importante: Use valores reais de vão, flecha e ângulo para resultados precisos.
          </p>
        </div>
      </div>
    ),
    current: 4,
    total: 5,
    isLast: false
  },
  {
    title: '4. Visualize o Resultado',
    content: (
      <div>
        <p className="text-gray-600 mb-4">
          O resultado é mostrado em três formatos: diagrama de relógio, tabela de cargas e valores detalhados.
        </p>
        <div className="flex space-x-2">
          <div className="bg-green-100 p-2 rounded text-xs text-center flex-1">🕐 Relógio</div>
          <div className="bg-blue-100 p-2 rounded text-xs text-center flex-1">📊 Tabela</div>
          <div className="bg-purple-100 p-2 rounded text-xs text-center flex-1">📈 Valores</div>
        </div>
      </div>
    ),
    current: 5,
    total: 5,
    isLast: true
  }
]
```

### 🔴 Alto (Impacto Alto/Esf. Médio)

#### 4. **Visualização de Dados Limitada**
```jsx
// PROBLEMA: Diagrama estático
// Sem interatividade
// Sem zoom/pan
// Sem export de visualizações
```

**Solução**: Visualização Interativa
```jsx
// components/Visualization/InteractiveDiagram.jsx
import React, { useState, useRef, useEffect } from 'react'
import { ZoomIn, ZoomOut, Download, RotateCcw, Maximize2 } from 'lucide-react'

const InteractiveDiagram = ({ data, onExport }) => {
  const [scale, setScale] = useState(1)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const svgRef = useRef(null)

  const handleZoomIn = () => setScale(prev => Math.min(prev + 0.1, 3))
  const handleZoomOut = () => setScale(prev => Math.max(prev - 0.1, 0.5))
  const handleReset = () => {
    setScale(1)
    setPosition({ x: 0, y: 0 })
  }

  const handleMouseDown = (e) => {
    setIsDragging(true)
    setDragStart({
      x: e.clientX - position.x,
      y: e.clientY - position.y
    })
  }

  const handleMouseMove = (e) => {
    if (isDragging) {
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      })
    }
  }

  const handleMouseUp = () => setIsDragging(false)

  const handleExport = () => {
    if (svgRef.current) {
      const svgData = new XMLSerializer().serializeToString(svgRef.current)
      const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' })
      const svgUrl = URL.createObjectURL(svgBlob)
      
      const img = new Image()
      img.onload = () => {
        const canvas = document.createElement('canvas')
        canvas.width = 800
        canvas.height = 600
        const ctx = canvas.getContext('2d')
        ctx.drawImage(img, 0, 0)
        
        canvas.toBlob((blob) => {
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = 'diagrama-calculo.png'
          a.click()
          URL.revokeObjectURL(url)
        })
      }
      img.src = svgUrl
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-lg border border-gray-200">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Diagrama de Tração</h3>
        <div className="flex items-center space-x-2">
          <button 
            onClick={handleZoomOut}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded"
            title="Diminuir zoom"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-sm font-medium text-gray-700 min-w-[3rem] text-center">
            {Math.round(scale * 100)}%
          </span>
          <button 
            onClick={handleZoomIn}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded"
            title="Aumentar zoom"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button 
            onClick={handleReset}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded"
            title="Resetar visualização"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <div className="w-px h-6 bg-gray-300" />
          <button 
            onClick={handleExport}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded"
            title="Exportar imagem"
          >
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Diagram Container */}
      <div 
        className="relative overflow-hidden bg-gray-50"
        style={{ height: '500px' }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <svg
          ref={svgRef}
          className="absolute inset-0 cursor-move"
          style={{
            transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
            transformOrigin: 'center'
          }}
          viewBox="-200 -200 400 400"
        >
          {/* Grid */}
          <defs>
            <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#e5e7eb" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect x="-200" y="-200" width="400" height="400" fill="url(#grid)" />
          
          <!-- Diagram content here -->
          <circle cx="0" cy="0" r="150" fill="none" stroke="#374151" strokeWidth="2" />
          
          {/* Force vectors */}
          {data.vectors.map((vector, index) => (
            <g key={index}>
              <line
                x1="0"
                y1="0"
                x2={vector.comp_x * 100}
                y2={-vector.comp_y * 100}
                stroke={getVectorColor(index)}
                strokeWidth="3"
                markerEnd="url(#arrowhead)"
              />
              <text
                x={vector.comp_x * 110}
                y={-vector.comp_y * 110}
                textAnchor="middle"
                className="text-sm font-medium fill-gray-700"
              >
                {vector.label}
              </text>
            </g>
          ))}
          
          {/* Arrow marker */}
          <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="#374151" />
            </marker>
          </defs>
        </svg>
      </div>

      {/* Info Panel */}
      <div className="p-4 bg-gray-50 border-t border-gray-200">
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <span className="font-medium text-gray-700">Tração Total:</span>
            <span className="ml-2 text-gray-900">{data.total_tracao_dan.toFixed(2)} daN</span>
          </div>
          <div>
            <span className="font-medium text-gray-700">Ângulo Resultante:</span>
            <span className="ml-2 text-gray-900">{data.total_angulo_graus.toFixed(1)}°</span>
          </div>
          <div>
            <span className="font-medium text-gray-700">Poste:</span>
            <span className="ml-2 text-gray-900">{data.poste.tipo_poste} {data.poste.modelo_poste}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
```

#### 5. **Formulários Não Otimizados**
```jsx
// PROBLEMA: UX de forms pobre
// Sem validação em tempo real
// Sem autofill inteligente
// Sem ajuda contextual
```

**Solução**: Smart Forms
```jsx
// components/Forms/SmartInput.jsx
import React, { useState, useEffect } from 'react'
import { AlertCircle, CheckCircle, HelpCircle } from 'lucide-react'

const SmartInput = ({ 
  label, 
  type = 'text', 
  value, 
  onChange, 
  validation,
  helpText,
  suggestions = [],
  unit,
  min,
  max,
  step = 'any'
}) => {
  const [focused, setFocused] = useState(false)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [validationState, setValidationState] = useState({ valid: true, message: '' })

  useEffect(() => {
    if (validation && value) {
      const result = validation(value)
      setValidationState(result)
    }
  }, [value, validation])

  const handleChange = (e) => {
    const newValue = e.target.value
    onChange(newValue)
    
    if (suggestions.length > 0 && newValue.length > 0) {
      setShowSuggestions(true)
    }
  }

  const handleSuggestionClick = (suggestion) => {
    onChange(suggestion.value)
    setShowSuggestions(false)
  }

  const inputClasses = `
    w-full px-4 py-2 border rounded-lg transition-all duration-200
    ${focused ? 'border-blue-500 ring-2 ring-blue-100' : 'border-gray-300'}
    ${validationState.valid ? 'focus:border-blue-500' : 'border-red-500 ring-2 ring-red-100'}
    ${!validationState.valid ? 'bg-red-50' : 'bg-white'}
  `

  return (
    <div className="relative">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
        {helpText && (
          <div className="inline-block ml-1 text-gray-400" title={helpText}>
            <HelpCircle className="w-4 h-4" />
          </div>
        )}
      </label>
      
      <div className="relative">
        <input
          type={type}
          value={value}
          onChange={handleChange}
          onFocus={() => setFocused(true)}
          onBlur={() => {
            setFocused(false)
            setTimeout(() => setShowSuggestions(false), 200)
          }}
          className={inputClasses}
          min={min}
          max={max}
          step={step}
        />
        
        {unit && (
          <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 text-sm">
            {unit}
          </span>
        )}
        
        {!validationState.valid && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-red-500">
            <AlertCircle className="w-4 h-4" />
          </div>
        )}
        
        {validationState.valid && value && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-green-500">
            <CheckCircle className="w-4 h-4" />
          </div>
        )}
      </div>

      {/* Suggestions Dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-auto">
          {suggestions
            .filter(s => s.label.toLowerCase().includes(value.toLowerCase()))
            .map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                className="w-full px-4 py-2 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
              >
                <div className="font-medium">{suggestion.label}</div>
                {suggestion.description && (
                  <div className="text-sm text-gray-500">{suggestion.description}</div>
                )}
              </button>
            ))}
        </div>
      )}

      {/* Validation Message */}
      {!validationState.valid && (
        <div className="mt-1 text-sm text-red-600 flex items-center">
          <AlertCircle className="w-3 h-3 mr-1" />
          {validationState.message}
        </div>
      )}

      {/* Help Text */}
      {helpText && focused && (
        <div className="mt-1 text-sm text-gray-500 bg-blue-50 p-2 rounded">
          {helpText}
        </div>
      )}
    </div>
  )
}

// Usage example
const TravessiaForm = () => {
  const [formData, setFormData] = useState({
    tipo_rede: '',
    tipo_cabo: '',
    vao: '',
    flecha: '',
    angulo: ''
  })

  const validateVao = (value) => {
    const num = parseFloat(value)
    if (isNaN(num)) return { valid: false, message: 'Valor deve ser numérico' }
    if (num < 1) return { valid: false, message: 'Vão mínimo: 1m' }
    if (num > 200) return { valid: false, message: 'Vão máximo: 200m' }
    return { valid: true }
  }

  const caboSuggestions = [
    { label: 'CA-50', value: 'CA-50', description: 'Cabo alumínio 50mm²' },
    { label: 'CA-70', value: 'CA-70', description: 'Cabo alumínio 70mm²' },
    { label: 'CA-95', value: 'CA-95', description: 'Cabo alumínio 95mm²' }
  ]

  return (
    <div className="space-y-4">
      <SmartInput
        label="Vão"
        type="number"
        value={formData.vao}
        onChange={(value) => setFormData({...formData, vao: value})}
        validation={validateVao}
        helpText="Distância horizontal entre postes (metros)"
        unit="m"
        min="1"
        max="200"
        step="0.5"
      />
      
      <SmartInput
        label="Tipo de Cabo"
        value={formData.tipo_cabo}
        onChange={(value) => setFormData({...formData, tipo_cabo: value})}
        suggestions={caboSuggestions}
        helpText="Selecione o tipo de cabo conforme catálogo"
      />
    </div>
  )
}
```

### 🟡 Médio (Impacto Médio/Esf. Baixo)

#### 6. **Dashboard Analytics Ausente**
```jsx
// PROBLEMA: Sem visão gerencial
// Sem métricas de uso
// Sem insights para usuário
```

**Solução**: Analytics Dashboard
```jsx
// components/Dashboard/AnalyticsDashboard.jsx
import React, { useState } from 'react'
import { BarChart3, TrendingUp, Clock, Users, Zap, Activity } from 'lucide-react'

const AnalyticsDashboard = ({ data }) => {
  const [period, setPeriod] = useState('7d')

  const metrics = [
    {
      title: 'Projetos Ativos',
      value: data.totalProjetos,
      change: '+12%',
      icon: <Users className="w-5 h-5" />,
      color: 'blue'
    },
    {
      title: 'Cálculos Realizados',
      value: data.totalCalculos,
      change: '+23%',
      icon: <Zap className="w-5 h-5" />,
      color: 'green'
    },
    {
      title: 'Tempo Médio',
      value: `${data.tempoMedio}min`,
      change: '-8%',
      icon: <Clock className="w-5 h-5" />,
      color: 'yellow'
    },
    {
      title: 'Taxa de Sucesso',
      value: `${data.taxaSucesso}%`,
      change: '+5%',
      icon: <Activity className="w-5 h-5" />,
      color: 'purple'
    }
  ]

  return (
    <div className="space-y-6">
      {/* Period Selector */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Dashboard Analytics</h2>
        <div className="flex bg-gray-100 rounded-lg p-1">
          {['24h', '7d', '30d', '90d'].map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                period === p 
                  ? 'bg-white text-gray-900 shadow-sm' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {p === '24h' ? '24 horas' : p === '7d' ? '7 dias' : p === '30d' ? '30 dias' : '90 dias'}
            </button>
          ))}
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric, index) => (
          <div key={index} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div className={`p-2 rounded-lg bg-${metric.color}-100 text-${metric.color}-600`}>
                {metric.icon}
              </div>
              <span className={`text-sm font-medium ${
                metric.change.startsWith('+') ? 'text-green-600' : 'text-red-600'
              }`}>
                {metric.change}
              </span>
            </div>
            <div className="mt-4">
              <h3 className="text-2xl font-bold text-gray-900">{metric.value}</h3>
              <p className="text-sm text-gray-600 mt-1">{metric.title}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Cálculos por Dia</h3>
          <div className="h-64 flex items-center justify-center text-gray-500">
            <BarChart3 className="w-8 h-8 mr-2" />
            Gráfico de cálculos diários
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Tipos de Poste</h3>
          <div className="h-64 flex items-center justify-center text-gray-500">
            <TrendingUp className="w-8 h-8 mr-2" />
            Distribuição de tipos de poste
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Atividade Recente</h3>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            {data.recentActivity.map((activity, index) => (
              <div key={index} className="flex items-center space-x-3">
                <div className={`w-2 h-2 rounded-full bg-${activity.color}-500`} />
                <div className="flex-1">
                  <p className="text-sm text-gray-900">{activity.description}</p>
                  <p className="text-xs text-gray-500">{activity.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
```

## 🎯 Oportunidades de UX

### 1. **Dark Mode**
```jsx
// hooks/useDarkMode.js
import { useState, useEffect } from 'react'

export const useDarkMode = () => {
  const [isDark, setIsDark] = useState(() => {
    return localStorage.getItem('darkMode') === 'true'
  })

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    localStorage.setItem('darkMode', isDark)
  }, [isDark])

  const toggle = () => setIsDark(!isDark)

  return { isDark, toggle }
}
```

### 2. **Progressive Web App**
```javascript
// PWA features
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js')
}

// Install prompt
let deferredPrompt
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault()
  deferredPrompt = e
  // Show install button
})

// Share API
const shareResult = async (data) => {
  if (navigator.share) {
    try {
      await navigator.share({
        title: 'Resultado do Cálculo de Tração',
        text: `Tração total: ${data.total_tracao_dan} daN`,
        url: window.location.href
      })
    } catch (err) {
      console.log('Share cancelled')
    }
  }
}
```

### 3. **Gestos e Atalhos**
```jsx
// Keyboard shortcuts
useEffect(() => {
  const handleKeyDown = (e) => {
    if (e.ctrlKey || e.metaKey) {
      switch (e.key) {
        case 's':
          e.preventDefault()
          handleSave()
          break
        case 'Enter':
          e.preventDefault()
          handleCalculate()
          break
        case 'z':
          e.preventDefault()
          handleUndo()
          break
      }
    }
  }

  window.addEventListener('keydown', handleKeyDown)
  return () => window.removeEventListener('keydown', handleKeyDown)
}, [])
```

## 📱 Mobile UX Enhancements

### 1. **Touch Optimization**
```css
/* Better touch targets */
@media (pointer: coarse) {
  .btn, .input, button {
    min-height: 44px;
    min-width: 44px;
  }
  
  .clickable {
    padding: 8px;
  }
}

/* Haptic feedback */
@supports (haptic: vibrate) {
  .btn:active {
    /* Trigger haptic feedback via JavaScript */
  }
}
```

### 2. **Swipe Gestures**
```jsx
// Mobile swipe navigation
import { useSwipeable } from 'react-swipeable'

const SwipeableContainer = ({ children, onSwipeLeft, onSwipeRight }) => {
  const handlers = useSwipeable({
    onSwipedLeft: onSwipeLeft,
    onSwipedRight: onSwipeRight,
    preventDefaultTouchmoveEvent: true,
    trackMouse: true
  })

  return <div {...handlers}>{children}</div>
}
```

## 🔧 Plano de Implementação UX

### Sprint 1 (Crítico)
1. Implementar Design System completo
2. Adicionar sistema de feedback visual
3. Criar onboarding estruturado

### Sprint 2 (Alto)
1. Desenvolver visualizações interativas
2. Implementar smart forms
3. Adicionar analytics dashboard

### Sprint 3 (Médio)
1. Implementar dark mode
2. Adicionar PWA features
3. Otimizar mobile UX

## 🚀 Recomendações Finais

### Imediatas
- **Prioridade 1**: Design System
- **Prioridade 2**: Feedback visual
- **Investimento**: 35-50 horas

### Longo Prazo
- **AI-powered suggestions**
- **Real-time collaboration**
- **Advanced visualizations**

---

**Status**: 🟡 **Requer Atenção Moderada**  
**Prioridade**: Média-Alta  
**Investimento Estimado**: 50-70 horas  
**ROI Esperado**: 3.5x (usabilidade + satisfação)
