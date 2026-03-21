# RAG/MEMORY.md - Contexto do Projeto Cálculo de Tração Light

## 📋 VISÃO GERAL DO PROJETO

**Nome**: Cálculo de Tração Light  
**Tipo**: Sistema de Engenharia Elétrica para Cálculo de Tração em Redes Aéreas  
**Arquitetura**: Thin Frontend / Smart Backend com DDD  
**Stack**: React + FastAPI + PostgreSQL + Redis + Ollama  
**Branch**: `dev` (única branch de desenvolvimento)

## 🎯 OBJETIVO PRINCIPAL

Sistema especializado para cálculo de tração em redes elétricas aéreas, focado em:
- Cálculos estruturais de postes e cabos
- Validação conforme normas técnicas brasileiras
- Otimização de projetos de distribuição
- Geração de relatórios técnicos
- Assistência inteligente via IA

## 🏗️ ARQUITETURA E PRINCÍPIOS

### Domain-Driven Design (DDD)
```
python/
├── domain/           # Domínio principal (lógica de negócio)
├── application/      # Casos de uso e orquestração
├── infrastructure/   # Implementações técnicas
├── interfaces/       # APIs e interfaces externas
└── shared/          # Domínios compartilhados
```

### Separação de Responsabilidades
- **Frontend**: React 2.5D, UI/UX em pt-BR, thin client
- **Backend**: FastAPI, business logic, inteligência
- **Database**: PostgreSQL + Redis para cache
- **AI**: Ollama local, zero custo monetário
- **Cache**: Redis para performance
- **Monitoring**: Sistema completo de métricas

## 🔧 REGRAS NÃO NEGOCIÁVEIS

### ✅ IMPLEMENTAÇÕES OBRIGATÓRIAS
1. **Branch Única**: Desenvolvimento apenas em `dev`
2. **RAG/MEMORY.md**: Este arquivo deve ser lido/entendido antes de qualquer task
3. **Dados Reais**: Sem dados mockados, usar apenas dados reais
4. **2.5D**: Visualização 2.5D em todo o projeto (sem 3D)
5. **Modularidade**: Arquivos >500 linhas devem ser modularizados
6. **Clean Code**: Código limpo, legível e manutenível
7. **Segurança**: Implementada em todas as camadas
8. **Testes**: Unitários + E2E com coverage mínimo 80%
9. **Docker First**: Containerização obrigatória
10. **pt-BR**: Interface em português brasileiro
11. **Zero Custo**: APIs gratuitas apenas

### 🎛️ ROLES ESPECÍFICOS
- **Tech Lead**: Orquestrador do desenvolvimento
- **Dev Fullstack Sênior**: Principal coder
- **DevOps/QA**: Testes e infraestrutura
- **UI/UX Designer**: Interfaces em pt-BR
- **Estagiário**: Criatividade e inovação

## 📊 ESTRUTURA DE DADOS

### Domínio Principal: Cálculo de Tração
```python
# Entidades principais
- Projeto: Informações do projeto elétrico
- Poste: Estruturas de suporte
- Cabo: Condutores elétricos
- Ponto: Pontos de cálculo específicos
- Tração: Resultados de cálculo
- Norma: Regras técnicas brasileiras
```

### Sanitização de Dados
- Validação em todas as entradas
- Conformidade com normas ABNT
- Verificação de unidades físicas
- Validação de faixas de valores
- Limpeza automática de dados

## 🚀 TECNOLOGIAS E FERRAMENTAS

### Backend (Smart)
- **FastAPI**: API REST com documentação automática
- **PostgreSQL**: Banco de dados principal
- **Redis**: Cache avançado
- **Ollama**: IA local (llama2, codellama, mistral)
- **Pydantic**: Validação de dados
- **SQLAlchemy**: ORM com DDD
- **Pytest**: Testes unitários

### Frontend (Thin)
- **React**: Interface 2.5D
- **Tailwind CSS**: Estilização
- **Vitest**: Testes unitários
- **Playwright**: Testes E2E
- **Lucide**: Ícones
- **pt-BR**: Localização obrigatória

### Infraestrutura
- **Docker**: Containerização
- **Docker Compose**: Orquestração local
- **GitHub Actions**: CI/CD
- **Redis**: Cache e sessões
- **Nginx**: Proxy reverso

## 📋 HALF-WAY BIM

### Implementação BIM Parcial
- **Modelagem 2.5D**: Visualização dimensional
- **Metadados técnicos**: Informações estruturadas
- **Coordenação**: Integração entre disciplinas
- **Documentação**: Relatórios técnicos automáticos
- **Colaboração**: Sistema multiusuário básico

### Features BIM
- Visualização de postes em 2.5D
- Análise de interferências
- Geração de plantas técnicas
- Cálculos automáticos integrados
- Relatórios conformidade ABNT

## 🧪 ESTRATÉGIA DE TESTES

### Coverage Requirements
- **20% de arquivos críticos**: 100% coverage
- **Demais arquivos**: Mínimo 80% coverage
- **Testes unitários**: Pytest + Vitest
- **Testes E2E**: Playwright
- **Testes de integração**: API completa

### Suíte de Testes
```bash
# Backend
pytest python/tests/ --cov=python --cov-report=html

# Frontend
npm run test:unit
npm run test:e2e

# Full suite
npm run test:all
```

## 🔐 SEGURANÇA

### Implementações
- **JWT**: Autenticação e autorização
- **Rate Limiting**: Proteção contra abuso
- **CORS**: Configuração restritiva
- **Headers**: Security headers completos
- **Input Validation**: Sanitização total
- **SQL Injection**: Proteção ORM
- **XSS**: Proteção frontend

### Políticas de Segurança
- Mínimo privilégio necessário
- Criptografia de dados sensíveis
- Logs de auditoria
- Monitoramento de segurança
- Atualizações automáticas

## 📈 PERFORMANCE E OTIMIZAÇÃO

### Estratégias
- **Cache Redis**: 60% melhoria em reads
- **Connection Pooling**: Otimização de banco
- **Lazy Loading**: Frontend otimizado
- **Code Splitting**: Módulos sob demanda
- **Compression**: Gzip automático
- **CDN**: Assets estáticos

### Métricas
- **Hit Rate**: >85% cache
- **Response Time**: <200ms API
- **Load Time**: <2s frontend
- **Memory**: <512MB por container
- **CPU**: <50% utilização

## 🌐 APIs EXTERNAS - ZERO CUSTO

### APIs Gratuitas Aprovadas
- **Ollama**: IA local (gratuito)
- **Open-Meteo**: Dados climáticos (gratuito)
- **IBGE API**: Dados geográficos (gratuito)
- **ViaCEP**: CEP brasileiro (gratuito)

### Proibido
- APIs pagas ou com limites estritos
- Serviços que gerem custos monetários
- Dependências externas críticas

## 📦 DOCKER FIRST

### Containerização Obrigatória
```dockerfile
# Multi-stage builds
# Alpine Linux base
# Security scanning
# Minimal layers
# Health checks
```

### Docker Compose
```yaml
# Serviços isolados
# Volumes persistentes
# Networks internas
# Environment vars
# Health checks
```

## 🎨 UI/UX - pt-BR OBRIGATÓRIO

### Interface em Português
- Todos os textos em pt-BR
- Formatos brasileiros (datas, números)
- Terminologia técnica brasileira
- Acessibilidade WCAG
- Design responsivo

### Padrões Visuais
- **Cores**: Azul (#2563eb) principal
- **Tipografia**: Inter ou similar
- **Ícones**: Lucide React
- **Layout**: Mobile-first
- **Componentes**: Reutilizáveis

## 🔄 FLUXO DE DESENVOLVIMENTO

### Processo Obrigatório
1. **Ler RAG/MEMORY.md** (antes de qualquer task)
2. **Executar testes** (sempre que necessário)
3. **Modularizar** (arquivos >500 linhas)
4. **Commit** (ao finalizar cada task)
5. **Branch dev** (única branch)

### Quality Gates
- ✅ Testes passando
- ✅ Coverage mínimo
- ✅ Code review
- ✅ Security scan
- ✅ Performance check

## 📋 CHECKLIST DE IMPLEMENTAÇÃO

### Para Cada Feature
- [ ] Leu RAG/MEMORY.md
- [ ] Implementou testes
- [ ] Coverage adequado
- [ ] Código limpo
- [ ] Documentado
- [ ] Segurança implementada
- [ ] Performance otimizada
- [ ] pt-BR implementado
- [ ] Docker configurado
- [ ] Commit realizado

## 🚨 REGRAS CRÍTICAS

### NUNCA FAZER
- ❌ Usar dados mockados
- ❌ Implementar 3D
- ❌ Usar APIs pagas
- ❌ Desenvolver em outras branches
- ❌ Ignorar testes
- ❌ Comitar sem testar
- ❌ Usar inglês na interface
- ❌ Ignorar segurança

### SEMPRE FAZER
- ✅ Ler RAG/MEMORY.md
- ✅ Testar tudo
- ✅ Modularizar código
- ✅ Usar pt-BR
- ✅ Implementar cache
- ✅ Otimizar performance
- ✅ Documentar código
- ✅ Usar Docker

## 📊 MÉTRICAS DE SUCESSO

### KPIs do Projeto
- **Performance**: <200ms response time
- **Coverage**: >80% test coverage
- **Security**: Zero vulnerabilidades críticas
- **Usability**: Interface pt-BR completa
- **Maintainability**: Código limpo e modular

### Monitoramento
- **APM**: Performance em tempo real
- **Logs**: Estruturados e centralizados
- **Alerts**: Automáticos e acionáveis
- **Dashboards**: Métricas visuais
- **Health Checks**: Automatizados

---

**IMPORTANTE**: Este documento é a fonte verdadeira do contexto do projeto. 
Sempre leia e entenda este arquivo antes de iniciar qualquer task de desenvolvimento.
