# Evidência de Smoke Mobile — Template

**Arquivo:** `docs/analises/mobile-smoke-<AAAA-MM-DD>-<responsavel>.md`  
**Propósito:** Registrar evidências do smoke test em dispositivo físico ou emulador de alta fidelidade exigidas pela seção 11.4 do `docs/frontend-qa-checklist.md`.

> **Instrução:** Copie este template, preencha cada seção e assine ao final. Arquive o documento preenchido em `docs/analises/` com o nome `mobile-smoke-AAAA-MM-DD-<responsavel>.md` **antes do merge para `main`**.

---

## 1. Identificação da Sessão de Smoke

| Campo | Valor |
|-------|-------|
| Data | |
| Responsável (nome + matrícula) | |
| Branch / commit SHA | |
| Versão frontend (package.json) | |

---

## 2. Dispositivos / Emuladores Testados

### 2.1 iOS

| Campo | Valor |
|-------|-------|
| Dispositivo / Emulador | _(ex: iPhone 15 Pro — iOS 17.4 ou Simulator Xcode 15.2 — iPhone SE iOS 17)_ |
| Viewport (px) | _(ex: 390 × 844 — logical)_ |
| Safari version | |
| PWA mode? | ☐ Sim ☐ Não |

### 2.2 Android

| Campo | Valor |
|-------|-------|
| Dispositivo / Emulador | _(ex: Pixel 7 — Android 14 ou Android Studio Emulator API 34)_ |
| Viewport (px) | _(ex: 360 × 800)_ |
| Chrome version | |
| PWA mode? | ☐ Sim ☐ Não |

---

## 3. Checklist de Cenários

Execute os cenários abaixo em cada dispositivo e marque o resultado.

### 3.1 Fluxo completo: Projeto → Ponto → Cálculo → Persistência

| # | Cenário | iOS ✓/✕ | Android ✓/✕ | Observação |
|---|---------|---------|------------|------------|
| 1 | Tela inicial carrega sem erro | | | |
| 2 | Campo Projeto preenche e confirma sem travar | | | |
| 3 | Campos de Ponto (nível, ângulo, vão) aceitam entrada numérica | | | |
| 4 | Teclado virtual não oculta o campo ativo | | | |
| 5 | ActionBar (CONFIRMAR) visível acima do teclado virtual | | | |
| 6 | Cálculo retorna resultado (tração total exibida) | | | |
| 7 | Status "Persistido" aparece após salvar | | | |
| 8 | Stepper condensado exibe etapa atual e próxima corretamente | | | |

### 3.2 Rolagem do formulário

| # | Cenário | iOS ✓/✕ | Android ✓/✕ | Observação |
|---|---------|---------|------------|------------|
| 9 | Formulário rola verticalmente sem travamento | | | |
| 10 | Scroll que começa sobre a ActionBar não trava a página | | | |
| 11 | Sem conteúdo oculto pelo header ou ActionBar fixos | | | |

### 3.3 APAGA com desfazer (UndoToast)

| # | Cenário | iOS ✓/✕ | Android ✓/✕ | Observação |
|---|---------|---------|------------|------------|
| 12 | Botão APAGA abre UndoToast com countdown | | | |
| 13 | "Desfazer" restaura dados dentro de 5 s | | | |
| 14 | Após timeout, campos são limpos e toast fecha | | | |

### 3.4 Usabilidade crítica

| # | Cenário | iOS ✓/✕ | Android ✓/✕ | Observação |
|---|---------|---------|------------|------------|
| 15 | Sem tap ignorado (botão responde ao toque) | | | |
| 16 | Sem conteúdo inacessível (campos fora da área de toque) | | | |
| 17 | Sem loop de estado (ex: spinner infinito, botão bloqueado) | | | |

---

## 4. Evidências Visuais

> Adicione capturas de tela ou link para gravação de tela abaixo.  
> Formato recomendado: `![descrição](path/to/screenshot.png)`

### iOS
_Adicionar screenshots/gravação aqui_

### Android
_Adicionar screenshots/gravação aqui_

---

## 5. Bloqueios de Usabilidade Crítica Encontrados

> Se nenhum bloqueio foi encontrado, escrever "Nenhum".

| # | Descrição | Dispositivo | Reprodução | Status |
|---|-----------|-------------|------------|--------|
| | | | | |

---

## 6. Resultado Geral

| Gate | Condição | Resultado |
|------|----------|-----------|
| Sem bloqueio crítico | Todos os cenários 15-17 ✓ em ambos os dispositivos | ☐ Aprovado ☐ Reprovado |
| Cobertura mínima | iOS + Android testados com evidência visual | ☐ Aprovado ☐ Reprovado |

**Conclusão:** ☐ **SMOKE PASSOU** — merge liberado ☐ **SMOKE FALHOU** — merge bloqueado

---

## 7. Assinatura do Responsável Técnico

Nome: _______________________________  
Matrícula: ___________________________  
Data: _______________________________  
Assinatura: __________________________

> Ao assinar, o responsável técnico declara que realizou ou supervisionou todos os cenários listados e que as evidências visuais são representativas da sessão de teste descrita acima.
