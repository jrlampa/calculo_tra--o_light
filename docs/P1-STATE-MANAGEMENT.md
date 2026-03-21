# P1 State Management: Undo + Mobile Action Bar

Documento tecnico do fluxo de estado entre telas para P1, cobrindo sincronizacao entre calculo, persistencia, undo e action bar mobile.

## 1. Diagrama de State Flow

```text
[Inputs UI]
  Header + SecaoNivel + selects poste + tabelas
      |
      v
[App local state]
  etapa, cabecalho, poste, mt1, mt2, bt, btz, ral
      |
      v (useMemo)
  formState
      |
      +------------------------------+
      | useCalculo(enabled=etapa==='calculo')
      | - debounce (600ms)
      | - abort request anterior
      +------------------------------+
                 |
                 v
        resultado + lastPayload
                 |
                 v
      +----------------------------------------------+
      | usePersistenciaCalculo({ pontoId, lastPayload, resultado })
      | - fila de persistencia (janela 5s)
      | - retry exponencial
      | - deteccao 403
      +----------------------------------------------+
                 |
                 v
 persistencia.status/error/canRetry/retryInSeconds
                 |
                 +--> Header (feedback + retry)
                 +--> FlowStepper (status de etapa)
                 +--> MobileActionBar (Confirmar/Reenviar/Proximo)

[useUndoStack(pontoId)]
  - stack local por ponto (undo/redo)
  - TTL 5 min
  - reset ao trocar pontoId
  - consumido por Ctrl+Z global (MVP: log, restore completo em V2)
```

### Exemplo de wiring no App

```jsx
const { resultado, loading, error, lastPayload } = useCalculo(formState, 600, etapa === 'calculo')

const { persistencia, resetPersistencia, flushPersistQueue } = usePersistenciaCalculo({
  pontoId: pontoAtual?.id,
  lastPayload,
  resultado,
})

const { undoStack, undo, push: pushUndo, canUndo } = useUndoStack(
  pontoAtual?.id,
  10,
  5 * 60 * 1000
)
```

## 2. State Management por Functional Area

## 2.1 useUndoStack (stack local, TTL, cleanup)

Responsabilidade:
- Manter historico local de alteracoes por ponto (undo/redo).
- Limitar tamanho da stack (max 10 no App).
- Expirar stack por TTL (5 minutos no App).
- Limpar estado ao trocar ponto (`pontoId`) e ao desmontar.

Estado interno:
- `undoStack` e `redoStack` em `useState`.
- `stackRef` para acesso sincronizado sem depender de render.
- `ttlTimerRef` para expiracao automatica.

Comportamento:
- `push(fieldKey, oldValue, newValue)` adiciona acao no topo, corta por `maxSize`, limpa redo.
- `undo()` remove a acao mais recente de undo e move para redo.
- `clear()` zera undo/redo/ref.
- TTL limpa ambas as stacks quando timer vence.

Exemplo de codigo:

```js
const push = useCallback((fieldKey, oldValue, newValue) => {
  const action = { timestamp: Date.now(), fieldKey, oldValue, newValue }
  const newUndoStack = [action, ...stackRef.current.undo].slice(0, maxSize)

  stackRef.current.undo = newUndoStack
  stackRef.current.redo = []
  stackRef.current.expiresAt = Date.now() + ttlMs

  setUndoStack(newUndoStack)
  setRedoStack([])
}, [maxSize, ttlMs])

useEffect(() => {
  if (undoStack.length > 0) {
    if (ttlTimerRef.current) clearTimeout(ttlTimerRef.current)
    ttlTimerRef.current = setTimeout(() => {
      setUndoStack([])
      setRedoStack([])
      stackRef.current = { undo: [], redo: [], expiresAt: null }
      ttlTimerRef.current = null
    }, ttlMs)
  }

  return () => {
    if (ttlTimerRef.current) {
      clearTimeout(ttlTimerRef.current)
      ttlTimerRef.current = null
    }
  }
}, [undoStack.length, ttlMs])
```

Observacao de implementacao:
- Hoje o listener global de Ctrl+Z no App chama `undo()`, mas a restauracao de campo ainda esta marcada como TODO (MVP faz log da acao).

## 2.2 usePersistenciaCalculo (fila, retry, 403, countdown)

Responsabilidade:
- Persistir resultado em fila com janela de 5s (`PERSIST_WINDOW_MS`) para reduzir burst de requests.
- Serializar operacoes para evitar concorrencia (`persistInFlightRef`).
- Fazer retry exponencial para erros transientes (ate 3 tentativas).
- Detectar 403/permissao e bloquear retry automatico.

Estado interno:
- `persistencia` (`status`, `error`, `willRetry`, `canRetry`, `isForbidden`, `retryInSeconds`).
- Refs de controle: `pendingPersistRef`, `lastPersistSignatureRef`, `lastPersistAtRef`, `retryCountRef`.
- Timers: `persistTimerRef` (fila/backoff) e `retryCountdownRef` (contador visual).

Regras principais:
- Novo calculo gera assinatura (`JSON.stringify(payload)`) para evitar persistencia duplicada.
- Se status for erro transiente: retry automatico com backoff exponencial.
- Se erro for 403: `isForbidden=true`, `willRetry=false`, `canRetry=true` (manual).

Exemplo de codigo:

```js
const isForbidden = err.status === 403 || err.isForbidden || err.code === 'FORBIDDEN'

if (isForbidden) {
  setPersistencia(prevState => ({
    ...prevState,
    status: 'error',
    error: err.message || 'Acesso negado',
    willRetry: false,
    canRetry: true,
    isForbidden: true,
    retryInSeconds: 0,
  }))
} else {
  retryCountRef.current += 1
  if (retryCountRef.current <= MAX_RETRIES) {
    const backoffMs = Math.min(1000 * 2 ** retryCountRef.current, 30_000)
    startRetryCountdown(backoffMs)
    setPersistencia(prevState => ({
      ...prevState,
      status: 'error',
      error: err.message,
      willRetry: true,
      canRetry: false,
      isForbidden: false,
    }))
    persistTimerRef.current = setTimeout(() => void flushPersistQueue(), backoffMs)
  }
}
```

## 2.3 useCalculo (computacao de formulario, debounced)

Responsabilidade:
- Observar `formState` e enviar POST para `/api/calcular` com debounce.
- Cancelar request anterior quando houver nova alteracao.
- Expor retorno normalizado para App (`resultado`, `loading`, `error`, `lastPayload`).

Comportamento:
- Ativo somente quando `enabled=true` (App ativa em `etapa === 'calculo'`).
- Ao desabilitar: limpa timer, aborta request, zera estados para evitar lixo de tela.

Exemplo de codigo:

```js
useEffect(() => {
  if (!enabled) {
    if (timerRef.current) clearTimeout(timerRef.current)
    if (abortRef.current) abortRef.current.abort()
    setLoading(false)
    setError(null)
    setResultado(null)
    setLastPayload(null)
    return undefined
  }

  if (timerRef.current) clearTimeout(timerRef.current)

  timerRef.current = setTimeout(async () => {
    if (abortRef.current) abortRef.current.abort()
    const controller = new AbortController()
    abortRef.current = controller

    const payload = buildCalculoRequest(formState)
    const response = await fetch('/api/calcular', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    })

    const data = await response.json()
    setResultado(data)
    setLastPayload(payload)
  }, debounceMs)

  return () => {
    if (timerRef.current) clearTimeout(timerRef.current)
    if (abortRef.current) abortRef.current.abort()
  }
}, [debounceMs, enabled, formState])
```

## 2.4 App.jsx local state (etapa, cabecalho, poste, mt1, mt2, bt, btz, ral)

Estado local principal:
- `etapa`: controla render da tela inicial (`projeto`) versus tela de calculo.
- `cabecalho`: dados de projeto/ponto exibidos no topo.
- `poste`: tipo/modelo do poste atual.
- `mt1`, `mt2`, `bt`, `btz`, `ral`: blocos de travessias do formulario tecnico.

Estados complementares relevantes para o fluxo:
- `projetoAtual`, `pontoAtual`, `pontoSnapshot`.
- `projetoState`, `pontoState`, `config`, `configState`.

Exemplo de codigo:

```jsx
const [etapa, setEtapa] = useState('projeto')
const [cabecalho, setCabecalho] = useState(() => ({ ...CABECALHO_INICIAL }))
const [poste, setPoste] = useState(() => ({ ...POSTE_INICIAL }))
const [mt1, setMT1] = useState(() => createTravessiasVazias(TRAVESSIA_MT_VAZIA))
const [mt2, setMT2] = useState(() => createTravessiasVazias(TRAVESSIA_MT_VAZIA))
const [bt, setBT] = useState(() => createTravessiasVazias(TRAVESSIA_MT_VAZIA))
const [btz, setBTZ] = useState(() => createTravessiasVazias(TRAVESSIA_BTZ_VAZIA))
const [ral, setRAL] = useState(() => createTravessiasVazias(TRAVESSIA_RAL_VAZIA))

const formState = useMemo(
  () => ({ cabecalho, poste, mt1, mt2, bt, btz, ral }),
  [cabecalho, poste, mt1, mt2, bt, btz, ral]
)
```

## 3. Entre-telas Flow (Projeto -> Ponto -> Calculo -> Persistido)

Fluxo funcional:
1. Projeto:
- `etapa='projeto'`.
- Usuario confirma projeto (`handleConfirmProjeto`), backend cria projeto e App troca para `etapa='calculo'`.

2. Ponto:
- Mesmo em `etapa='calculo'`, a subetapa de vinculo de ponto e controlada por `pontoState`/`pontoAtual`.
- `handleConfirmPonto` cria ponto no backend e ativa persistencia vinculada ao `pontoId`.

3. Calculo:
- Alteracoes de formulario disparam `useCalculo`.
- Resultado novo alimenta `usePersistenciaCalculo`.

4. Persistido:
- Quando `persistencia.status='saved'`, UI mostra sucesso e libera "Proximo Ponto".

Exemplo de codigo:

```jsx
const handleConfirmProjeto = async () => {
  const projetoCriado = await createProjeto(cabecalho)
  setProjetoAtual(projetoCriado)
  setCabecalho(prev => ({ ...prev, projeto: projetoCriado.nome || prev.projeto, ponto: '' }))
  setEtapa('calculo')
}

const handleConfirmPonto = async () => {
  const pontoCriado = await createPonto(projetoAtual.id, {
    ponto: (cabecalho.ponto || '').trim(),
    tipoPoste: poste.tipoPoste,
    modeloPoste: poste.modeloPoste,
  })
  setPontoAtual(pontoCriado)
  setPontoSnapshot({
    ponto: (cabecalho.ponto || '').trim(),
    tipoPoste: poste.tipoPoste || '',
    modeloPoste: poste.modeloPoste || '',
  })
  resetPersistencia()
}
```

Como o state persiste ao trocar etapa:
- A troca `projeto -> calculo` nao zera `cabecalho` e demais blocos tecnicos.
- O nome do projeto persiste e o campo `ponto` e limpo para forcar vinculacao explicita do novo ponto.

Como o state reseta ao trocar ponto:
- Troca manual de ponto/tipo/modelo apos confirmacao invalida o vinculo (`pontoSnapshot`), limpando `pontoAtual` e persistencia.
- `handleProximoPonto` limpa niveis tecnicos e contexto de ponto, mantendo projeto ativo.

Exemplo de reset por mudanca de ponto:

```jsx
useEffect(() => {
  if (!pontoSnapshot) return

  const pontoMudou = (cabecalho.ponto || '').trim() !== pontoSnapshot.ponto
  const tipoMudou = (poste.tipoPoste || '') !== pontoSnapshot.tipoPoste
  const modeloMudou = (poste.modeloPoste || '') !== pontoSnapshot.modeloPoste

  if (!pontoMudou && !tipoMudou && !modeloMudou) return

  setPontoAtual(null)
  setPontoSnapshot(null)
  setPontoState({ loading: false, status: 'idle', error: '' })
  resetPersistencia()
}, [cabecalho.ponto, pontoSnapshot, poste.modeloPoste, poste.tipoPoste, resetPersistencia])
```

## 4. Undo Stack State Transitions

Diagrama de transicao:

```text
[Idle - stack vazia]
   |
   | push(fieldKey, oldValue, newValue)
   v
[Action pushed - stack ativa]
   |
   | Ctrl+Z -> undo()
   v
[Undo triggered]
   |
   | (MVP) retorna action para o listener
   | (V2) aplica oldValue no campo de origem
   v
[Restored]
   |
   +--> se stack vazia: volta para Idle

Eventos de limpeza:
- TTL expirado -> Idle
- Mudanca de pontoId -> Idle
- clear() explicito -> Idle
```

Comportamento de TTL:
- O timer de expiracao limpa undo/redo e ref interna.
- `canUndo` e `canRedo` dependem da combinacao de stack nao vazia e `!isExpired`.

Exemplo de consumo via teclado global:

```jsx
useEffect(() => {
  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
      e.preventDefault()
      const action = undo()
      if (action) {
        console.log(`Undo: ${action.fieldKey} <- ${action.oldValue}`)
      }
    }
  }

  window.addEventListener('keydown', handleKeyDown)
  return () => window.removeEventListener('keydown', handleKeyDown)
}, [undo])
```

## 5. Mobile Action Bar State Binding

A action bar recebe estado ja derivado do App, baseado em `persistencia`.

Binding no App:

```jsx
<MobileActionBar
  onConfirm={() => flushPersistQueue()}
  onRetry={persistencia.canRetry ? flushPersistQueue : undefined}
  onNextPoint={persistencia.status === 'saved' ? handleProximoPonto : undefined}
  statusPersistencia={persistencia.status}
  canRetry={persistencia.canRetry && persistencia.status === 'error'}
  canNextPoint={persistencia.status === 'saved'}
  isDisabled={persistencia.status === 'saving'}
/>
```

Regra de visibilidade/acao:
- `Confirmar`: sempre renderizado; desabilitado em `saving`.
- `Reenviar`: renderizado somente quando `canRetry=true`.
- `Proximo ponto`: renderizado somente quando `canNextPoint=true` (status `saved`).

Exemplo interno do componente:

```jsx
const isSaving = statusPersistencia === 'saving' || isDisabled

<button onClick={onConfirm} disabled={isSaving}>✓ Confirmar</button>

{canRetry && (
  <button onClick={onRetry} disabled={isSaving}>↻ Reenviar</button>
)}

{canNextPoint && (
  <button onClick={onNextPoint} disabled={isSaving}>→ Prox. Ponto</button>
)}
```

Tabela de leitura rapida por status:

| statusPersistencia | canRetry | canNextPoint | Resultado na Mobile Action Bar |
|---|---:|---:|---|
| idle | false | false | So Confirmar |
| queued | false | false | So Confirmar |
| saving | false | false | Confirmar desabilitado |
| error (transiente esgotado) | true | false | Confirmar + Reenviar |
| error (403) | true | false | Confirmar + Reenviar (manual) |
| saved | false | true | Confirmar + Proximo ponto |

## 6. Cleanup & Memory Management

Pontos de cleanup implementados:
- `useCalculo`: limpa debounce timer e aborta fetch no cleanup do efeito.
- `usePersistenciaCalculo`: limpa timeout e interval (fila + countdown) no unmount/reset.
- `useUndoStack`: limpa timeout TTL ao trocar ponto e ao desmontar.
- `App`: remove listener global de teclado no cleanup.

Exemplo de cleanup por hook:

```js
// usePersistenciaCalculo
useEffect(() => {
  return () => {
    clearPersistTimer()
  }
}, [clearPersistTimer])

// useCalculo
return () => {
  if (timerRef.current) clearTimeout(timerRef.current)
  if (abortRef.current) abortRef.current.abort()
}
```

Validacao "no memory leaks" (estado atual do codigo):
- Timers/intervals relevantes possuem `clearTimeout`/`clearInterval`.
- Requests HTTP em progresso sao abortadas antes de nova execucao e no unmount.
- Listener global de teclado e removido corretamente.
- Refs de controle (`pendingPersistRef`, `persistInFlightRef`, `stackRef`) sao reinicializadas em reset.

Checklist rapido de verificacao manual:
1. Navegar entre projeto e calculo varias vezes e confirmar ausencia de listeners duplicados.
2. Alterar campos em alta frequencia e validar cancelamento de requests anteriores.
3. Simular erro de persistencia e observar se countdown para retry para apos reset/unmount.
4. Trocar de ponto e confirmar stack de undo vazia e sem timers ativos do ponto anterior.
