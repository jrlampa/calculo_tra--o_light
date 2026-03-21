# Tokens Visuais Frontend

## Direção visual
- Linguagem visual: técnico-operacional com DNA Excel e camada 2.5D discreta.
- Objetivo: máxima legibilidade para cálculo, com hierarquia de estados (loading, sucesso, erro) explícita.
- Princípio: não alterar semântica de workbook, apenas melhorar percepção, acessibilidade e previsibilidade de interação.

## Tokens semânticos

### Superfícies
| Token semântico | Valor base | CSS var | Tailwind |
| --- | --- | --- | --- |
| Surface glass | rgba(255, 255, 255, 0.72) | --glass-bg | colors.surface.glass |
| Surface glass strong | rgba(255, 255, 255, 0.84) | --glass-bg-strong | colors.surface.glass-strong |
| Surface panel sólido | #ffffff | --surface-solid-panel | colors.surface.panel |
| Surface input | rgba(245, 249, 255, 0.88) | --surface-input | colors.surface.input |
| Surface readonly | rgba(233, 240, 250, 0.95) | --surface-readonly | colors.surface.readonly |

### Estados
| Token semântico | Valor base | CSS var | Tailwind |
| --- | --- | --- | --- |
| Status loading background | rgba(255, 244, 228, 0.9) | --surface-saving | colors.status.loading |
| Status success background | rgba(236, 248, 236, 0.9) | --surface-saved | colors.status.success |
| Status error background | rgba(255, 237, 237, 0.92) | --surface-error | colors.status.error |
| Status loading text | #7f4b0f | n/a | colors.status.loading-text |
| Status success text | #24613a | n/a | colors.status.success-text |
| Status error text | #7f1f1f | n/a | colors.status.error-text |

### Ações
| Token semântico | Valor base | CSS var | Tailwind |
| --- | --- | --- | --- |
| Action primary end | #3b66ad | --btn-blue-end | colors.action.primary |
| Action primary hover end | #315998 | --btn-blue-hover-end | colors.action.primary-hover |
| Action secondary end | #bc5a17 | --btn-orange-end | colors.action.secondary |
| Action secondary hover end | #a84b11 | --btn-orange-hover-end | colors.action.secondary-hover |

### Bordas e foco
| Token semântico | Valor base | CSS var | Tailwind |
| --- | --- | --- | --- |
| Border soft | rgba(132, 154, 188, 0.46) | --glass-border | colors.border.soft |
| Border strong | rgba(112, 137, 176, 0.62) | --glass-border-strong | colors.border.strong |
| Focus border | #2f66c1 | --focus-border | colors.border.focus |
| Focus ring | rgba(46, 105, 196, 0.35) | --focus-ring | n/a |

### Sombra e raio
| Token semântico | Valor base | CSS var | Tailwind |
| --- | --- | --- | --- |
| Shadow glass | 0 10px 28px rgba(23, 46, 90, 0.14) | --glass-shadow | boxShadow.glass |
| Shadow glass soft | 0 4px 14px rgba(34, 57, 96, 0.1) | --glass-shadow-soft | boxShadow.glass-soft |
| Shadow action | 0 7px 16px rgba(52, 84, 139, 0.24) | n/a | boxShadow.action |
| Radius panel | 10px | n/a | borderRadius.panel |
| Radius card | 12px | n/a | borderRadius.card |
| Radius soft | 8px | n/a | borderRadius.soft |

## Tokens legados de cálculo
Estes tokens foram preservados para manter paridade visual com elementos técnicos da planilha:
- tracao-orange
- tracao-red
- tracao-blue
- tracao-green
- tracao-dark

## Mapeamento por componente
| Componente | Tokens principais | Intenção |
| --- | --- | --- |
| Banner de config | status.loading, status.error, border.soft/strong | Visibilidade de fallback sem competir com resultado técnico |
| Header status | status.loading/success/error + shadow.glass-soft | Estado operacional de ponto e persistência |
| Inputs técnicos | surface.input, border.focus, focus ring | Legibilidade e precisão de edição |
| Botões principais | action.primary/action.secondary | Diferenciar ação de confirmação e ação de limpeza |
| Painéis de seção | surface.glass + shadow.glass-soft + radius.soft | Agrupamento visual por bloco técnico |
| Resumo textual de gráfico | text-secondary + spacing compacto | Equivalência de leitura para assistivas |

## Regras de uso
- Usar token semântico antes de criar valor literal novo.
- Evitar mistura de tons fora da paleta definida neste documento.
- Qualquer novo estado visual deve nascer com paridade em CSS var e Tailwind.
- Em modo reduced motion, preservar feedback por cor/contraste sem depender de animação.
