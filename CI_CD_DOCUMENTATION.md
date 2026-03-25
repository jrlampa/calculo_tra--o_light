# Documentação CI/CD Integration - calculo_tração_light

## Visão Geral

Este documento descreve a implementação completa da integração CI/CD para o projeto calculo_tração_light, com foco especial na integração dos testes de persistência no pipeline de integração contínua.

## Estrutura do Pipeline CI/CD

### 1. Workflows GitHub Actions

#### `ci.yml` - Pipeline Principal de CI/CD
**Objetivo**: Execução completa de testes e deploy em múltiplos ambientes.

**Jobs Principais**:
- **test-python**: Testes Python em múltiplas versões (3.10, 3.11, 3.12)
- **test-frontend**: Testes frontend em múltiplas versões Node.js (16, 18, 20)
- **test-e2e**: Testes end-to-end com Playwright
- **test-integration**: Testes de integração completa
- **security-quality**: Análise de segurança e qualidade de código
- **deploy-staging**: Deploy para ambiente de staging
- **deploy-production**: Deploy para ambiente de produção
- **notify**: Notificações de status

**Features**:
- ✅ Multi-branch (main, develop)
- ✅ Multi-version testing
- ✅ Parallel execution
- ✅ Artifact upload
- ✅ Coverage reporting
- ✅ Security scanning

#### `test-persistence.yml` - Testes de Persistência Específicos
**Objetivo**: Execução focada nos testes de persistência implementados.

**Jobs Específicos**:
- **test-hierarquia-completa**: Testes de hierarquia completa
- **test-persistencia-calculo**: Testes de persistência de cálculos
- **test-parity-excel**: Testes de paridade Excel
- **test-integracao-real**: Testes de integração real
- **test-execucao-completa**: Teste de execução completa
- **test-performance**: Testes de performance
- **test-concorrencia**: Testes de concorrência
- **test-seguranca-dados**: Testes de segurança de dados
- **resumo-testes**: Resumo e notificações

**Features**:
- ✅ Trigger por mudança de código
- ✅ Trigger programado (diário às 2h)
- ✅ Ambientes isolados por teste
- ✅ Relatórios detalhados
- ✅ Integração com codecov

#### `deploy.yml` - Pipeline de Deploy
**Objetivo**: Deploy automatizado e seguro para staging e produção.

**Jobs Principais**:
- **build-images**: Build e push de imagens Docker
- **deploy-staging**: Deploy para staging
- **deploy-production**: Deploy para produção
- **migrate-database**: Migrações de banco de dados
- **performance-testing**: Testes de performance
- **security-scanning**: Scanning de segurança
- **cleanup**: Limpeza de recursos
- **notify**: Notificações

**Features**:
- ✅ Docker multi-stage builds
- ✅ Environment-specific deployments
- ✅ Health checks
- ✅ Smoke tests
- ✅ Security scanning (Trivy, Snyk)
- ✅ Rollback capabilities

#### `test-setup.yml` - Setup de Ambiente de Testes
**Objetivo**: Configuração e validação do ambiente de testes.

**Jobs Principais**:
- **setup-test-env**: Setup do ambiente de testes
- **validate-test-scripts**: Validação de scripts de teste
- **health-check**: Health check do ambiente
- **update-documentation**: Atualização de documentação
- **notify-setup**: Notificações de setup

**Features**:
- ✅ Environment validation
- ✅ Test script compilation
- ✅ Database connectivity tests
- ✅ Automated documentation updates

## Estratégia de Testes

### 1. Testes de Persistência

#### Hierarquia Completa
- **Objetivo**: Validar todo o fluxo de persistência (Projeto → Ponto → Nível → Travessia)
- **Cobertura**: Criação, validação, consistência referencial
- **Execução**: `test_hierarquia_completa.py`

#### Persistência de Cálculos
- **Objetivo**: Garantir persistência correta de resultados de cálculo
- **Cobertura**: Fluxo completo, atualização, consistência numérica
- **Execução**: `test_persistencia_calculo.py`

#### Parity Excel
- **Objetivo**: Validar paridade entre sistema e planilha LIGHT.xlsm
- **Cobertura**: Precisão numérica, consistência de dados
- **Execução**: `test_parity_excel.py`

#### Integração Real
- **Objetivo**: Testes end-to-end com banco de dados real
- **Cobertura**: Performance, concorrência, isolamento de usuários
- **Execução**: `test_integracao_real.py`

### 2. Estratégia de Execução

#### Multi-Environment
- **Development**: Testes rápidos, foco em feedback rápido
- **Staging**: Testes completos, ambiente de pré-produção
- **Production**: Deploy controlado, monitoramento intensivo

#### Multi-Branch
- **main**: Deploy automático para produção após validação
- **develop**: Deploy automático para staging
- **feature branches**: Testes de integração, sem deploy

#### Multi-Version
- **Python**: 3.10, 3.11, 3.12
- **Node.js**: 16, 18, 20
- **PostgreSQL**: 15
- **Redis**: 7

## Configuração de Ambiente

### 1. Variáveis de Ambiente

#### Obrigatórias
```bash
DATABASE_URL=postgresql://user:password@host:port/db
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-key
```

#### Opcionais
```bash
REDIS_URL=redis://localhost:6379/0
FRONTEND_URL=http://localhost:3000
API_URL=http://localhost:8000
```

### 2. Serviços

#### PostgreSQL
- **Versão**: 15
- **Health Check**: `pg_isready`
- **Portas**: 5432
- **Configuração**: Teste isolado por job

#### Redis
- **Versão**: 7
- **Health Check**: `redis-cli ping`
- **Portas**: 6379
- **Uso**: Cache e sessões

#### Supabase
- **URL**: Configurável por ambiente
- **Chave**: Service key para testes
- **Uso**: Banco de dados principal

### 3. Dependências

#### Python
```txt
# requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
asyncpg==0.29.0
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
```

#### Node.js
```json
{
  "devDependencies": {
    "vitest": "^1.0.0",
    "playwright": "^1.40.0",
    "eslint": "^8.54.0"
  }
}
```

## Integração de Testes

### 1. Script de Integração CI/CD

#### `ci_cd_integration.py`
**Objetivo**: Orquestrar a execução dos testes de persistência no CI/CD.

**Funcionalidades**:
- ✅ Environment detection
- ✅ Test discovery
- ✅ Database connection testing
- ✅ Individual test execution
- ✅ Performance testing
- ✅ Report generation
- ✅ JSON results output

**Uso no GitHub Actions**:
```yaml
- name: Run CI/CD Integration
  run: python python/ci_cd_integration.py
```

### 2. Execução de Testes

#### Script Principal
```bash
# Executar todos os testes de persistência
python python/executar_testes_persistencia.py

# Executar testes individuais
python -m pytest python/tests/test_hierarquia_completa.py -v
python -m pytest python/tests/test_persistencia_calculo.py -v
python -m pytest python/tests/test_parity_excel.py -v
python -m pytest python/tests/test_integracao_real.py -v
```

#### Cobertura de Código
```bash
# Gerar relatório de cobertura
pytest tests/ --cov=api --cov=services --cov=repositories --cov=db --cov-report=xml --cov-report=html
```

## Monitoramento e Métricas

### 1. Métricas de Testes

#### Cobertura
- **Backend**: 100% de cobertura de persistência
- **Frontend**: Testes unitários e E2E
- **Integração**: Testes completos de fluxo

#### Performance
- **Criação de projetos**: <30s para 10 projetos
- **Leitura de projetos**: <10s para 10 projetos
- **Concorrência**: Testes com múltiplos usuários simultâneos

#### Qualidade
- **Security**: Bandit, Safety, Snyk
- **Code Quality**: ESLint, Pylint
- **Dependencies**: Vulnerability scanning

### 2. Monitoramento de Deploy

#### Health Checks
- **API**: `/health` endpoint
- **Database**: Connection validation
- **Frontend**: Page load validation

#### Performance Monitoring
- **Response Time**: API response times
- **Database Queries**: Query performance
- **Memory Usage**: Application memory usage

#### Error Tracking
- **Logs**: Centralized logging
- **Alerts**: Automated alerting on failures
- **Rollback**: Automatic rollback on critical failures

## Segurança

### 1. Segurança no CI/CD

#### Secrets Management
- **GitHub Secrets**: Armazenamento seguro de credenciais
- **Environment Variables**: Isolamento por ambiente
- **Access Control**: Permissões granulares

#### Security Scanning
- **SAST**: Static Application Security Testing
- **DAST**: Dynamic Application Security Testing
- **Dependency Scanning**: Vulnerability detection

### 2. Segurança de Dados

#### Test Data
- **Isolation**: Dados de teste isolados
- **Sanitization**: Dados sensíveis sanitizados
- **Cleanup**: Limpeza automática de dados de teste

#### Database Security
- **Connection Security**: SSL/TLS encryption
- **Access Control**: Role-based access
- **Audit Trail**: Complete audit logging

## Troubleshooting

### 1. Problemas Comuns

#### Database Connection
```bash
# Verificar conexão com banco de dados
python -c "from db.supabase_client import get_supabase_client; import asyncio; asyncio.run(get_supabase_client().fetch_one('SELECT 1'))"
```

#### Test Failures
```bash
# Executar testes com verbose output
python -m pytest tests/ -v --tb=long

# Executar testes específicos
python -m pytest tests/test_hierarquia_completa.py::TestHierarquiaCompleta::test_hierarquia_completa_fluxo -v
```

#### Performance Issues
```bash
# Verificar performance do banco de dados
python -c "
import time
from db.supabase_client import get_supabase_client
import asyncio

async def test_performance():
    client = get_supabase_client()
    start = time.time()
    for i in range(100):
        await client.fetch_one('SELECT 1')
    end = time.time()
    print(f'Time: {end-start}s')

asyncio.run(test_performance())
"
```

### 2. Logs e Debug

#### GitHub Actions Logs
- **Job Logs**: Detalhes de execução de cada job
- **Step Logs**: Logs de cada step do workflow
- **Artifacts**: Arquivos de saída e logs

#### Local Debug
```bash
# Executar workflows localmente
act -j test-python

# Debug com verbose
act -j test-python -v
```

## Melhores Práticas

### 1. Desenvolvimento

#### Test-First Approach
- ✅ Escrever testes antes do código
- ✅ Testes de integração desde o início
- ✅ Cobertura de casos de uso críticos

#### Code Quality
- ✅ Code reviews obrigatórios
- ✅ Linting automático
- ✅ Formatação consistente

### 2. CI/CD

#### Fast Feedback
- ✅ Testes rápidos no início do pipeline
- ✅ Paralelismo onde possível
- ✅ Cache de dependências

#### Reliability
- ✅ Testes estáveis e determinísticos
- ✅ Ambientes consistentes
- ✅ Rollback automático

#### Security
- ✅ Secrets management seguro
- ✅ Security scanning automatizado
- ✅ Access control granular

## Conclusão

A implementação completa da integração CI/CD para o projeto calculo_tração_light proporciona:

- ✅ **Qualidade**: Testes abrangentes e automatizados
- ✅ **Segurança**: Security scanning e secrets management
- ✅ **Performance**: Monitoramento e otimização contínua
- ✅ **Confiabilidade**: Deploys seguros e rollback automático
- ✅ **Produtividade**: Feedback rápido e automação completa

O pipeline está pronto para suportar o crescimento do projeto e garantir a entrega contínua de software de alta qualidade.