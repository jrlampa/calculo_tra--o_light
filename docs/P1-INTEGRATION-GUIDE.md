# P1 Integration Guide: Undo + Mobile Action Bar

## Pré-requisitos
- ✅ src/hooks/useUndoStack.js exists
- ✅ src/components/actionBar/MobileActionBar.jsx exists
- ✅ src/components/tabela/TabelaCarga.jsx updated
- ✅ tailwind.config.js updated with safe-area plugins
- ✅ e2e/ui-undo-mobile.spec.js exists

## Step 1: Adicionar Imports em src/App.jsx

Localize a seção de imports (primeiras ~20 linhas) e adicione:

```jsx
import useUndoStack from './hooks/useUndoStack.js'
import MobileActionBar from './components/actionBar/MobileActionBar.jsx'
```

## Step 2: Instanciar Hooks (dentro da função App())

Após a linha que instancia `usePersistenciaCalculo`, adicione:

```jsx
  // Undo stack hook: max 10 ações por ponto, TTL 5 minutos
  const { undoStack, undo, push: pushUndo, canUndo } = useUndoStack(
    pontoAtual?.id,
    10,
    5 * 60 * 1000
  )
```

## Step 3: Adicionar Global Ctrl+Z Listener

Após o useEffect de `loadConfig`, adicione novo useEffect:

```jsx
  // Global Ctrl+Z listener para undo
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
        e.preventDefault()
        const action = undo()
        if (action) {
          // MVP: apenas log do undo. Em V2, restaurar field específico
          console.log(`Undo: ${action.fieldKey} ← ${action.oldValue}`)
          // TODO: mapear action.fieldKey para setState específico
          // Ex: if (action.fieldKey === 'numero_vao') setNumeroVao(action.oldValue)
        }
      }
    }
    
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [undo])
```

## Step 4: Renderizar MobileActionBar (condicional na etapa 'calculo')

Localize aonde atualmente `<TabelaCarga>` é renderizada (deve estar perto de fim do JSX de App, dentro de `etapa === 'calculo'`).

**Após** a TabelaCarga, adicione:

```jsx
      {/* Mobile Action Bar — visível apenas na etapa calculo */}
      {etapa === 'calculo' && (
        <MobileActionBar
          onConfirm={() => flushPersistQueue()}
          onRetry={persistencia.canRetry ? flushPersistQueue : undefined}
          onNextPoint={persistencia.status === 'saved' ? handleProximoPonto : undefined}
          statusPersistencia={persistencia.status}
          canRetry={persistencia.canRetry && persistencia.status === 'error'}
          canNextPoint={persistencia.status === 'saved'}
          isDisabled={persistencia.status === 'saving'}
        />
      )}
```

## Step 5: Validação Pré-PR

Antes de submeter PR, confirme:

- [ ] `npm run build` passa sem errors
- [ ] No new console.log statements (remover linhas debug)
- [ ] `npm run test:e2e` roda sem falhas (esperar ~60s)
- [ ] Testado em desktop (Chrome DevTools device emulation)
- [ ] Testado em mobile (<640px viewport)
- [ ] Testado em tablet (768px breakpoint)
- [ ] Ctrl+Z key listener funciona (listener adiciona/remove corretamente)
- [ ] MobileActionBar não sobrepõe TabelaCarga (margin-bottom: 20)
- [ ] Safe-area CSS funciona em iPhone (se houver device real)

## Próximos Passos

1. Copiar 4 trechos de código acima (Imports, Hook, Listener, Render)
2. Colar em App.jsx nos locais indicados
3. Executar checklist de validação
4. Submeter PR com branch name: `feat/p1-undo-mobile-action-bar`

## Notas Técnicas

### Undo Stack Behavior
- Max 10 ações por ponto (limite de memória)
- TTL 5 minutos (auto-clear após inatividade)
- Auto-clear ao trocar de ponto (useEffect observa pontoAtual?.id)
- Redo stack também gerenciado (push nova ação limpa redo)

### MobileActionBar Responsiveness
- Desktop (≥1024px): fixed floating corner (bottom-right)
- Tablet (640-1023px): full-width bottom bar com labels
- Mobile (<640px): stacked vertical com ícones (44px+ height)
- Safe-area inset handled via CSS `env(safe-area-inset-bottom)`

### TabelaCarga Mobile Optimization
- Mobile: margin-bottom: 20 (60vh para tabela + 20vh action bar)
- Mobile: overflow-x-auto (scroll horizontal sem truncation)
- Mobile: font text-[8px] vs desktop text-[9px]
- No breaking changes em desktop layout
