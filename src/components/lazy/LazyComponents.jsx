/* This code snippet is utilizing lazy loading in a React application to improve performance by loading
components only when they are needed. Here's a breakdown of what the code is doing: */
import React, { Suspense, lazy } from 'react'
import LoadingSpinner from '../ui/LoadingSpinner.jsx'

// Lazy loading para componentes pesados
const LazyTabelaCarga = lazy(() => 
  import('../tabela/TabelaCarga.jsx').then(module => ({
    default: module.default
  }))
)

const LazyDiagramaPoste = lazy(() => 
  import('../relogio/DiagramaPoste.jsx').then(module => ({
    default: module.default
  }))
)

const LazyRelogioAngulos = lazy(() => 
  import('../relogio/RelogioAngulos.jsx').then(module => ({
    default: module.default
  }))
)

const LazyMobileActionBar = lazy(() => 
  import('../actionBar/MobileActionBar.jsx').then(module => ({
    default: module.default
  }))
)

// Wrapper components com loading
const LazyTabelaCargaWrapper = (props) => (
  <Suspense fallback={<LoadingSpinner message="Carregando tabela de cargas..." />}>
    <LazyTabelaCarga {...props} />
  </Suspense>
)

const LazyDiagramaPosteWrapper = (props) => (
  <Suspense fallback={<LoadingSpinner message="Carregando diagrama do poste..." />}>
    <LazyDiagramaPoste {...props} />
  </Suspense>
)

const LazyRelogioAngulosWrapper = (props) => (
  <Suspense fallback={<LoadingSpinner message="Carregando relógio de ângulos..." />}>
    <LazyRelogioAngulos {...props} />
  </Suspense>
)

const LazyMobileActionBarWrapper = (props) => (
  <Suspense fallback={<LoadingSpinner message="Carregando barra de ações..." />}>
    <LazyMobileActionBar {...props} />
  </Suspense>
)

// Preload components para melhor performance
const preloadComponent = (componentImporter) => {
  componentImporter()
}

const preloadAllComponents = () => {
  preloadComponent(() => import('../tabela/TabelaCarga.jsx'))
  preloadComponent(() => import('../relogio/DiagramaPoste.jsx'))
  preloadComponent(() => import('../relogio/RelogioAngulos.jsx'))
  preloadComponent(() => import('../actionBar/MobileActionBar.jsx'))
}

export {
  LazyTabelaCargaWrapper as LazyTabelaCarga,
  LazyDiagramaPosteWrapper as LazyDiagramaPoste,
  LazyRelogioAngulosWrapper as LazyRelogioAngulos,
  LazyMobileActionBarWrapper as LazyMobileActionBar,
  preloadAllComponents
}
