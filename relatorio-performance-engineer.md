# Relatório Técnico - Performance Engineer

## 📊 Análise de Performance

### Stack de Performance Atual
- **Frontend**: React + Vite (✅ otimizado)
- **Backend**: FastAPI (sem otimização)
- **Database**: Supabase (sem tuning)
- **Caching**: Ausente (❌)
- **Monitoring**: Básico (❌)
- **Optimization**: Manual (❌)

### 🏗️ Arquitetura de Performance

```
Performance Issues:
├── Frontend (React)
│   ├── App.jsx monstro (575 linhas) 🚨
│   ├── Re-renders excessivos 🚨
│   ├── Bundle size médio (181KB) ⚠️
│   └── Sem lazy loading ⚠️
├── Backend (FastAPI)
│   ├── api/main.py monstro (611 linhas) 🚨
│   ├── Queries N+1 🚨
│   ├── Sem cache 🚨
│   └── Sem connection pooling ⚠️
├── Database (Supabase)
│   ├── Sem índices otimizados 🚨
│   ├── Queries lentas 🚨
│   └── Sem monitoring ⚠️
└── Infrastructure
    ├── Sem CDN ⚠️
    ├── Sem load balancing ⚠️
    └── Deploy manual ⚠️
```

## ⚠️ Problemas Críticos Identificados

### 🚨 Crítico (Impacto Alto/Esf. Baixo)

#### 1. **Frontend Performance Crítica**
```jsx
// PROBLEMA: App.jsx com 15+ useState hooks
// Re-renders em cascata
// Sem memoização adequada
// Performance impact severo
```

**Solução Imediata**: Otimização Agressiva
```jsx
// hooks/useOptimizedCalculoState.js
import { useState, useCallback, useMemo } from 'react'
import { debounce } from 'lodash-es'

// Estado particionado para reduzir re-renders
const useOptimizedCalculoState = () => {
  // Estados agrupados por frequência de atualização
  const [projetoState, setProjetoState] = useState({
    etapa: 'projeto',
    projetoAtual: null,
    projetoState: { loading: false, error: '' }
  })
  
  const [pontoState, setPontoState] = useState({
    pontoAtual: null,
    pontoSnapshot: null,
    pontoState: { loading: false, status: 'idle', error: '' }
  })
  
  const [formState, setFormState] = useState({
    cabecalho: CABECALHO_INICIAL,
    poste: POSTE_INICIAL,
    mt1: createTravessiasVazias(TRAVESSIA_MT_VAZIA),
    mt2: createTravessiasVazias(TRAVESSIA_MT_VAZIA),
    bt: createTravessiasVazias(TRAVESSIA_MT_VAZIA),
    btz: createTravessiasVazias(TRAVESSIA_BTZ_VAZIA),
    ral: createTravessiasVazias(TRAVESSIA_RAL_VAZIA)
  })
  
  // Memoização pesada para cálculos complexos
  const formStateMemo = useMemo(() => {
    // Apenas recalcula quando formState mudar
    return {
      ...formState,
      // Cálculos pesados aqui
      totalTravessias: Object.values(formState).reduce((sum, travessia) => 
        sum + (travessia?.length || 0), 0
      ),
      hasData: Object.values(formState).some(travessia => 
        travessia?.some(item => item.vao > 0)
      )
    }
  }, [formState])
  
  // Debounced updates para inputs frequentes
  const debouncedFormUpdate = useCallback(
    debounce((updates) => {
      setFormState(prev => ({ ...prev, ...updates }))
    }, 300),
    []
  )
  
  return {
    // Estados particionados
    projetoState,
    pontoState,
    formState: formStateMemo,
    
    // Actions otimizadas
    setProjetoState,
    setPontoState,
    updateForm: debouncedFormUpdate,
    
    // Selectores memoizados
    selectors: {
      hasUnsavedChanges: useMemo(() => {
        // Lógica complexa para detectar mudanças
        return false // Implementar
      }, [formStateMemo])
    }
  }
}

// Componentes otimizados com React.memo
const OptimizedTabelaCarga = React.memo(({ dados, onRowClick }) => {
  // Virtual scrolling para grandes tabelas
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: 50 })
  
  const visibleData = useMemo(() => 
    dados.slice(visibleRange.start, visibleRange.end),
    [dados, visibleRange]
  )
  
  // Intersection Observer para lazy loading
  const observerRef = useRef()
  
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            // Carregar mais dados
            setVisibleRange(prev => ({
              ...prev,
              end: Math.min(prev.end + 50, dados.length)
            }))
          }
        })
      },
      { threshold: 0.1 }
    )
    
    if (observerRef.current) {
      observer.observe(observerRef.current)
    }
    
    return () => observer.disconnect()
  }, [dados.length])
  
  return (
    <div className="overflow-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="bg-gray-100">
            <th className="p-2">Nível</th>
            <th className="p-2">Rede</th>
            <th className="p-2">Cabo</th>
            <th className="p-2">Vão (m)</th>
            <th className="p-2">Flecha (m)</th>
            <th className="p-2">Ângulo (°)</th>
            <th className="p-2">Tração (daN)</th>
          </tr>
        </thead>
        <tbody>
          {visibleData.map((row, index) => (
            <OptimizedTableRow 
              key={row.id || index}
              data={row}
              onClick={onRowClick}
            />
          ))}
        </tbody>
      </table>
      <div ref={observerRef} className="h-4" />
    </div>
  )
})

const OptimizedTableRow = React.memo(({ data, onClick }) => (
  <tr 
    className="hover:bg-gray-50 cursor-pointer border-b"
    onClick={() => onClick(data)}
  >
    <td className="p-2">{data.nivel}</td>
    <td className="p-2">{data.rede}</td>
    <td className="p-2">{data.cabo}</td>
    <td className="p-2">{data.vao}</td>
    <td className="p-2">{data.flecha}</td>
    <td className="p-2">{data.angulo}</td>
    <td className="p-2 font-medium">{data.tracao?.toFixed(2)}</td>
  </tr>
))
```

#### 2. **Backend Performance Crítica**
```python
# PROBLEMA: api/main.py com lógica síncrona
# Queries N+1 em cascata
# Sem cache de resultados
# Bottleneck severo
```

**Solução**: Backend Otimizado
```python
# performance/optimized_calculo_service.py
import asyncio
import time
from typing import List, Dict, Any
from functools import lru_cache
import redis
from dataclasses import dataclass

@dataclass
class PerformanceMetrics:
    calculation_time: float
    query_time: float
    cache_hit_rate: float
    memory_usage: float

class OptimizedCalculoService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.cache_ttl = 3600  # 1 hora
        self.metrics = PerformanceMetrics(0, 0, 0, 0)
    
    async def calcular_polo_otimizado(self, input_data: CalculoInput) -> CalculoOutput:
        """Cálculo otimizado com cache e paralelização"""
        start_time = time.time()
        
        # Cache key baseada no hash dos inputs
        cache_key = self._generate_cache_key(input_data)
        
        # Tentar cache primeiro
        cached_result = await self._get_cached_result(cache_key)
        if cached_result:
            self.metrics.cache_hit_rate = (
                self.metrics.cache_hit_rate * 0.9 + 1.0 * 0.1
            )  # Moving average
            return cached_result
        
        # Paralelizar cálculos independentes
        tasks = [
            self._calcular_mt_async(input_data.mt1),
            self._calcular_mt_async(input_data.mt2),
            self._calcular_bt_async(input_data.bt),
            self._calcular_btz_async(input_data.btz),
            self._calcular_ral_async(input_data.ral)
        ]
        
        # Executar em paralelo
        mt1_result, mt2_result, bt_result, btz_result, ral_result = await asyncio.gather(*tasks)
        
        # Combinar resultados
        combined_result = self._combine_results([
            mt1_result, mt2_result, bt_result, btz_result, ral_result
        ])
        
        # Cache do resultado
        await self._cache_result(cache_key, combined_result)
        
        # Atualizar métricas
        self.metrics.calculation_time = time.time() - start_time
        
        return combined_result
    
    async def _calcular_mt_async(self, mt_inputs: List[MTTraversalInput]) -> LevelResult:
        """Cálculo MT assíncrono otimizado"""
        if not mt_inputs:
            return self._empty_result()
        
        # Processar em batch se houver muitos inputs
        if len(mt_inputs) > 5:
            return await self._process_batch_mt(mt_inputs)
        
        # Cálculo individual para poucos inputs
        tasks = [self._calcular_single_mt_async(mt) for mt in mt_inputs]
        results = await asyncio.gather(*tasks)
        
        return self._combine_mt_results(results)
    
    @lru_cache(maxsize=1000)
    def _get_poste_data(self, tipo_poste: str, modelo_poste: str) -> Dict[str, Any]:
        """Cache em memória para dados de postes"""
        # Buscar do banco (implementar)
        return {"altura": 12, "carga_admissivel": 3000}
    
    async def _get_cached_result(self, cache_key: str) -> Optional[CalculoOutput]:
        """Buscar resultado do cache Redis"""
        try:
            cached = await self.redis.get(cache_key)
            if cached:
                return CalculoOutput.parse_raw(cached)
        except Exception as e:
            logger.error(f"Cache error: {e}")
        return None
    
    async def _cache_result(self, cache_key: str, result: CalculoOutput):
        """Armazenar resultado no cache"""
        try:
            await self.redis.setex(
                cache_key, 
                self.cache_ttl, 
                result.json()
            )
        except Exception as e:
            logger.error(f"Cache storage error: {e}")
    
    def _generate_cache_key(self, input_data: CalculoInput) -> str:
        """Gerar chave de cache única"""
        import hashlib
        import json
        
        # Normalizar inputs para cache consistente
        normalized = {
            "mt1": [{"vao": round(mt.vao, 2), "angulo": round(mt.angulo, 1)} for mt in input_data.mt1],
            "mt2": [{"vao": round(mt.vao, 2), "angulo": round(mt.angulo, 1)} for mt in input_data.mt2],
            "bt": [{"vao": round(bt.vao, 2), "angulo": round(bt.angulo, 1)} for bt in input_data.bt],
            "btz": [{"vao": round(btz.vao, 2)} for btz in input_data.btz],
            "ral": [{"vao": round(ral.vao, 2)} for ral in input_data.ral],
            "poste": f"{input_data.poste.tipo_poste}_{input_data.poste.modelo_poste}"
        }
        
        json_str = json.dumps(normalized, sort_keys=True)
        return hashlib.md5(json_str.encode()).hexdigest()

# Database otimizado com connection pooling
class OptimizedDatabaseService:
    def __init__(self):
        self.pool = None  # Configurar connection pool
    
    async def get_projetos_with_stats_otimizado(self, user_id: str) -> List[Dict]:
        """Query otimizada com JOIN e agregação"""
        query = """
        SELECT 
            p.id,
            p.nome,
            p.created_at,
            COUNT(pt.id) as total_pontos,
            COUNT(c.id) as total_calculos,
            AVG(c.total_tracao_dan) as avg_tracao,
            MAX(c.created_at) as last_calculo
        FROM projetos p
        LEFT JOIN pontos pt ON p.id = pt.projeto_id
        LEFT JOIN calculos c ON pt.id = c.ponto_id
        WHERE p.owner_id = $1
        GROUP BY p.id, p.nome, p.created_at
        ORDER BY p.created_at DESC
        LIMIT 100
        """
        
        start_time = time.time()
        result = await self.pool.fetch(query, user_id)
        query_time = time.time() - start_time
        
        # Log performance
        if query_time > 0.5:  # Alerta se query lenta
            logger.warning(f"Slow query detected: {query_time:.2f}s")
        
        return [dict(row) for row in result]
    
    async def batch_insert_calculos(self, calculos: List[Dict]) -> bool:
        """Insert em batch para melhor performance"""
        if not calculos:
            return True
        
        # Preparar dados para batch insert
        values = []
        for calc in calculos:
            values.append(f"('{calc['ponto_id']}', '{calc['dados']}', '{calc['created_at']}')")
        
        query = f"""
        INSERT INTO calculos (ponto_id, dados, created_at)
        VALUES {','.join(values)}
        ON CONFLICT (ponto_id) DO UPDATE SET
            dados = EXCLUDED.dados,
            created_at = EXCLUDED.created_at
        """
        
        try:
            await self.pool.execute(query)
            return True
        except Exception as e:
            logger.error(f"Batch insert error: {e}")
            return False
```

#### 3. **Database Performance Crítica**
```sql
-- PROBLEMA: Queries lentas sem índices
-- Full table scans
-- Sem query optimization
-- Performance degradada
```

**Solução**: Database Otimizado
```sql
-- Índices estratégicos para performance
CREATE INDEX CONCURRENTLY idx_projetos_owner_created 
ON projetos(owner_id, created_at DESC);

CREATE INDEX CONCURRENTLY idx_pontos_projeto_ponto 
ON pontos(projeto_id, ponto);

CREATE INDEX CONCURRENTLY idx_calculos_ponto_created 
ON calculos(ponto_id, created_at DESC);

CREATE INDEX CONCURRENTLY idx_calculos_ponto_tracao 
ON calculos(ponto_id) INCLUDE (total_tracao_dan, total_angulo_graus);

-- Índices compostos para queries comuns
CREATE INDEX CONCURRENTLY idx_projetos_owner_stats 
ON projetos(owner_id) INCLUDE (nome, created_at);

-- Partitioning para tabelas grandes (calculos)
CREATE TABLE calculos_partitioned (
    LIKE calculos INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- Partições mensais
CREATE TABLE calculos_2024_01 PARTITION OF calculos_partitioned
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE calculos_2024_02 PARTITION OF calculos_partitioned
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Materialized views para relatórios
CREATE MATERIALIZED VIEW projeto_stats_mv AS
SELECT 
    p.id,
    p.nome,
    COUNT(DISTINCT pt.id) as total_pontos,
    COUNT(DISTINCT c.id) as total_calculos,
    AVG(c.total_tracao_dan) as avg_tracao,
    MAX(c.created_at) as last_activity,
    p.created_at as project_created
FROM projetos p
LEFT JOIN pontos pt ON p.id = pt.projeto_id
LEFT JOIN calculos c ON pt.id = c.ponto_id
GROUP BY p.id, p.nome, p.created_at;

-- Índice para materialized view
CREATE INDEX idx_projeto_stats_mv_activity 
ON projeto_stats_mv(last_activity DESC);

-- Function para refresh automático
CREATE OR REPLACE FUNCTION refresh_projeto_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY projeto_stats_mv;
END;
$$ LANGUAGE plpgsql;

-- Trigger para refresh periódico (via cron job)
-- Ou implementar via application

-- Query optimization examples
EXPLAIN (ANALYZE, BUFFERS) 
SELECT p.*, COUNT(pt.id) as ponto_count
FROM projetos p
LEFT JOIN pontos pt ON p.id = pt.projeto_id
WHERE p.owner_id = 'user_id'
GROUP BY p.id
ORDER BY p.created_at DESC;

-- Otimized query with proper indexes
EXPLAIN (ANALYZE, BUFFERS)
SELECT p.*, COUNT(pt.id) as ponto_count
FROM projetos p
LEFT JOIN pontos pt ON p.id = pt.projeto_id
WHERE p.owner_id = 'user_id'
GROUP BY p.id, p.nome, p.created_at
ORDER BY p.created_at DESC
LIMIT 50;
```

### 🔴 Alto (Impacto Alto/Esf. Médio)

#### 4. **Cache Strategy Ausente**
```python
# PROBLEMA: Sem camada de cache
-- Requests repetitivos desnecessários
-- Load excessivo no database
-- Performance degradada
```

**Solução**: Multi-Layer Cache
```python
# cache/multi_layer_cache.py
import asyncio
import json
import time
from typing import Any, Optional, Dict
from abc import ABC, abstractmethod
import redis
from functools import wraps

class CacheLayer(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass

class MemoryCache(CacheLayer):
    """Cache em memória para dados frequentes"""
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key in self.cache:
                item = self.cache[key]
                if time.time() < item['expires']:
                    return item['value']
                else:
                    del self.cache[key]
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        async with self._lock:
            if len(self.cache) >= self.max_size:
                # LRU: remover item mais antigo
                oldest_key = min(self.cache.keys(), 
                               key=lambda k: self.cache[k]['created'])
                del self.cache[oldest_key]
            
            self.cache[key] = {
                'value': value,
                'expires': time.time() + (ttl or self.default_ttl),
                'created': time.time()
            }
            return True
    
    async def delete(self, key: str) -> bool:
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

class RedisCache(CacheLayer):
    """Redis cache para persistência e distribuição"""
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        try:
            serialized = json.dumps(value, default=str)
            await self.redis.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

class MultiLayerCache:
    """Cache multi-layer: Memory -> Redis -> Database"""
    def __init__(self, redis_client: redis.Redis):
        self.memory_cache = MemoryCache(max_size=1000, default_ttl=300)
        self.redis_cache = RedisCache(redis_client)
        self.stats = {
            'memory_hits': 0,
            'redis_hits': 0,
            'misses': 0
        }
    
    async def get(self, key: str) -> Optional[Any]:
        # Layer 1: Memory cache
        value = await self.memory_cache.get(key)
        if value is not None:
            self.stats['memory_hits'] += 1
            return value
        
        # Layer 2: Redis cache
        value = await self.redis_cache.get(key)
        if value is not None:
            self.stats['redis_hits'] += 1
            # Promote to memory cache
            await self.memory_cache.set(key, value, ttl=300)
            return value
        
        # Cache miss
        self.stats['misses'] += 1
        return None
    
    async def set(self, key: str, value: Any, memory_ttl: int = 300, redis_ttl: int = 3600) -> bool:
        # Set em ambos os layers
        memory_success = await self.memory_cache.set(key, value, ttl=memory_ttl)
        redis_success = await self.redis_cache.set(key, value, ttl=redis_ttl)
        return memory_success and redis_success
    
    async def delete(self, key: str) -> bool:
        memory_success = await self.memory_cache.delete(key)
        redis_success = await self.redis_cache.delete(key)
        return memory_success or redis_success
    
    def get_stats(self) -> Dict[str, int]:
        total = sum(self.stats.values())
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            'hit_rate': (self.stats['memory_hits'] + self.stats['redis_hits']) / total,
            'memory_hit_rate': self.stats['memory_hits'] / total,
            'redis_hit_rate': self.stats['redis_hits'] / total
        }

# Cache decorator para funções
def cached(ttl: int = 3600, key_prefix: str = ""):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Gerar chave de cache
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Tentar cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Executar função
            result = await func(*args, **kwargs)
            
            # Cache do resultado
            await cache.set(cache_key, result, ttl=ttl)
            
            return result
        return wrapper
    return decorator

# Uso nos serviços
class OptimizedProjetoService:
    def __init__(self, cache: MultiLayerCache):
        self.cache = cache
    
    @cached(ttl=1800, key_prefix="projeto")
    async def get_projeto_with_stats(self, projeto_id: str) -> Dict[str, Any]:
        """Get projeto com stats cacheado por 30 minutos"""
        # Query otimizada com JOIN
        query = """
        SELECT p.*, COUNT(pt.id) as total_pontos,
               COUNT(c.id) as total_calculos,
               AVG(c.total_tracao_dan) as avg_tracao
        FROM projetos p
        LEFT JOIN pontos pt ON p.id = pt.projeto_id
        LEFT JOIN calculos c ON pt.id = c.ponto_id
        WHERE p.id = $1
        GROUP BY p.id
        """
        
        result = await self.db.fetchrow(query, projeto_id)
        return dict(result) if result else None
    
    async def invalidate_projeto_cache(self, projeto_id: str):
        """Invalidar cache quando projeto é atualizado"""
        patterns = [
            f"projeto:get_projeto_with_stats:{hash(projeto_id)}",
            f"projeto:list_projetos:*",
            f"projeto:get_projeto_stats:{hash(projeto_id)}"
        ]
        
        for pattern in patterns:
            await self.cache.delete(pattern)
```

#### 5. **Frontend Bundle Optimization**
```javascript
// PROBLEMA: Bundle size médio (181KB)
// Sem code splitting
// Sem tree shaking adequado
// Performance impact em mobile
```

**Solução**: Bundle Optimization
```javascript
// vite.config.js - Otimizado para performance
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  
  // Build otimizado
  build: {
    target: 'esnext',
    minify: 'terser',
    sourcemap: false,
    
    // Code splitting agressivo
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor libraries
          vendor: ['react', 'react-dom'],
          
          // UI libraries
          ui: ['lucide-react'],
          
          // Utilities
          utils: ['lodash-es'],
          
          // Charts/visualizations
          charts: []
        },
        
        // Nomes de files otimizados
        chunkFileNames: (chunkInfo) => {
          const facadeModuleId = chunkInfo.facadeModuleId ? chunkInfo.facadeModuleId.split('/').pop() : 'chunk'
          return `js/[name]-[hash].js`
        },
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.')
          const ext = info[info.length - 1]
          if (/\.(mp4|webm|ogg|mp3|wav|flac|aac)(\?.*)?$/i.test(assetInfo.name)) {
            return `media/[name]-[hash][extname]`
          }
          if (/\.(png|jpe?g|gif|svg|webp|avif)(\?.*)?$/i.test(assetInfo.name)) {
            return `images/[name]-[hash][extname]`
          }
          if (/\.(woff2?|eot|ttf|otf)(\?.*)?$/i.test(assetInfo.name)) {
            return `fonts/[name]-[hash][extname]`
          }
          return `assets/[name]-[hash][extname]`
        }
      }
    },
    
    // Tamanhos de chunk
    chunkSizeWarningLimit: 1000,
    
    // CSS optimization
    cssCodeSplit: true
  },
  
  // Development otimizado
  server: {
    port: 5173,
    host: true,
    cors: true
  },
  
  // Dependencies optimization
  optimizeDeps: {
    include: ['react', 'react-dom', 'lucide-react'],
    exclude: ['@supabase/supabase-js']
  },
  
  // Resolve paths
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@hooks': resolve(__dirname, 'src/hooks'),
      '@utils': resolve(__dirname, 'src/utils')
    }
  }
})

// Lazy loading components
import { lazy, Suspense } from 'react'
import LoadingSpinner from './components/ui/LoadingSpinner'

// Lazy loading para componentes pesados
const DiagramaPoste = lazy(() => import('./components/relogio/DiagramaPoste'))
const TabelaCarga = lazy(() => import('./components/tabela/TabelaCarga'))
const AnalyticsDashboard = lazy(() => import('./components/dashboard/AnalyticsDashboard'))

// Component wrapper com loading
const LazyWrapper = ({ children, fallback = <LoadingSpinner /> }) => (
  <Suspense fallback={fallback}>
    {children}
  </Suspense>
)

// Usage no App.jsx
const App = () => {
  const [etapa, setEtapa] = useState('projeto')
  
  return (
    <div className="app">
      {/* Componentes críticos carregados normalmente */}
      <Header />
      <FlowStepper etapa={etapa} />
      
      {/* Componentes pesados com lazy loading */}
      {etapa === 'calculo' && (
        <LazyWrapper>
          <DiagramaPoste data={diagramaData} />
        </LazyWrapper>
      )}
      
      {etapa === 'calculo' && (
        <LazyWrapper>
          <TabelaCarga dados={tabelaDados} />
        </LazyWrapper>
      )}
      
      {/* Dashboard apenas quando necessário */}
      {showDashboard && (
        <LazyWrapper>
          <AnalyticsDashboard />
        </LazyWrapper>
      )}
    </div>
  )
}

// Service Worker para cache offline
// public/sw.js
const CACHE_NAME = 'calculo-tracao-v1'
const STATIC_ASSETS = [
  '/',
  '/manifest.json',
  '/assets/css/main.css',
  '/assets/js/main.js'
]

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(STATIC_ASSETS))
  )
})

self.addEventListener('fetch', (event) => {
  // Network first para API
  if (event.request.url.includes('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // Cache successful responses
          if (response.ok) {
            const responseClone = response.clone()
            caches.open(CACHE_NAME)
              .then((cache) => cache.put(event.request, responseClone))
          }
          return response
        })
        .catch(() => {
          // Fallback to cache
          return caches.match(event.request)
        })
    )
  }
  
  // Cache first para assets estáticos
  else {
    event.respondWith(
      caches.match(event.request)
        .then((response) => {
          return response || fetch(event.request)
        })
    )
  }
})
```

### 🟡 Médio (Impacto Médio/Esf. Baixo)

#### 6. **Monitoring de Performance**
```python
# PROBLEMA: Sem métricas de performance
# Sem alertas de degradação
# Impossível otimizar proativamente
```

**Solução**: Performance Monitoring
```python
# monitoring/performance_monitor.py
import time
import psutil
import asyncio
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from prometheus_client import Counter, Histogram, Gauge, generate_latest

@dataclass
class PerformanceMetrics:
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    active_connections: int
    avg_response_time: float
    requests_per_second: float
    cache_hit_rate: float
    database_query_time: float

class PerformanceMonitor:
    def __init__(self):
        # Prometheus metrics
        self.request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
        self.request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
        self.active_connections = Gauge('active_connections', 'Active database connections')
        self.cache_hits = Counter('cache_hits_total', 'Cache hits', ['cache_type'])
        self.cache_misses = Counter('cache_misses_total', 'Cache misses', ['cache_type'])
        self.db_query_duration = Histogram('db_query_duration_seconds', 'Database query duration')
        
        # Internal metrics
        self.metrics_history: List[PerformanceMetrics] = []
        self.max_history = 1000
        
        # Performance thresholds
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 90.0,
            'memory_warning': 80.0,
            'memory_critical': 95.0,
            'response_time_warning': 2.0,
            'response_time_critical': 5.0,
            'cache_hit_rate_warning': 0.5,
            'db_query_time_warning': 1.0
        }
    
    async def collect_metrics(self) -> PerformanceMetrics:
        """Coletar métricas de performance"""
        timestamp = time.time()
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Application metrics
        active_connections = self.get_active_connections()
        avg_response_time = self.get_avg_response_time()
        requests_per_second = self.get_requests_per_second()
        cache_hit_rate = self.get_cache_hit_rate()
        db_query_time = self.get_avg_db_query_time()
        
        metrics = PerformanceMetrics(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / 1024 / 1024,
            active_connections=active_connections,
            avg_response_time=avg_response_time,
            requests_per_second=requests_per_second,
            cache_hit_rate=cache_hit_rate,
            database_query_time=db_query_time
        )
        
        # Adicionar ao histórico
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history:
            self.metrics_history.pop(0)
        
        # Verificar thresholds e gerar alertas
        await self.check_thresholds(metrics)
        
        return metrics
    
    async def check_thresholds(self, metrics: PerformanceMetrics):
        """Verificar thresholds e gerar alertas"""
        alerts = []
        
        # CPU alerts
        if metrics.cpu_percent > self.thresholds['cpu_critical']:
            alerts.append({
                'level': 'CRITICAL',
                'metric': 'cpu',
                'value': metrics.cpu_percent,
                'threshold': self.thresholds['cpu_critical'],
                'message': f'CPU usage critical: {metrics.cpu_percent:.1f}%'
            })
        elif metrics.cpu_percent > self.thresholds['cpu_warning']:
            alerts.append({
                'level': 'WARNING',
                'metric': 'cpu',
                'value': metrics.cpu_percent,
                'threshold': self.thresholds['cpu_warning'],
                'message': f'CPU usage high: {metrics.cpu_percent:.1f}%'
            })
        
        # Memory alerts
        if metrics.memory_percent > self.thresholds['memory_critical']:
            alerts.append({
                'level': 'CRITICAL',
                'metric': 'memory',
                'value': metrics.memory_percent,
                'threshold': self.thresholds['memory_critical'],
                'message': f'Memory usage critical: {metrics.memory_percent:.1f}%'
            })
        elif metrics.memory_percent > self.thresholds['memory_warning']:
            alerts.append({
                'level': 'WARNING',
                'metric': 'memory',
                'value': metrics.memory_percent,
                'threshold': self.thresholds['memory_warning'],
                'message': f'Memory usage high: {metrics.memory_percent:.1f}%'
            })
        
        # Response time alerts
        if metrics.avg_response_time > self.thresholds['response_time_critical']:
            alerts.append({
                'level': 'CRITICAL',
                'metric': 'response_time',
                'value': metrics.avg_response_time,
                'threshold': self.thresholds['response_time_critical'],
                'message': f'Response time critical: {metrics.avg_response_time:.2f}s'
            })
        elif metrics.avg_response_time > self.thresholds['response_time_warning']:
            alerts.append({
                'level': 'WARNING',
                'metric': 'response_time',
                'value': metrics.avg_response_time,
                'threshold': self.thresholds['response_time_warning'],
                'message': f'Response time high: {metrics.avg_response_time:.2f}s'
            })
        
        # Enviar alertas
        for alert in alerts:
            await self.send_alert(alert)
    
    async def send_alert(self, alert: Dict[str, Any]):
        """Enviar alerta de performance"""
        logger.warning(f"Performance Alert [{alert['level']}]: {alert['message']}")
        
        # Integrar com sistema de notificações
        if alert['level'] == 'CRITICAL':
            await self.notify_team(alert)
    
    def get_performance_summary(self, minutes: int = 5) -> Dict[str, Any]:
        """Resumo de performance dos últimos N minutos"""
        cutoff_time = time.time() - (minutes * 60)
        recent_metrics = [
            m for m in self.metrics_history 
            if m.timestamp > cutoff_time
        ]
        
        if not recent_metrics:
            return {}
        
        return {
            'period_minutes': minutes,
            'samples': len(recent_metrics),
            'cpu': {
                'avg': sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
                'max': max(m.cpu_percent for m in recent_metrics),
                'min': min(m.cpu_percent for m in recent_metrics)
            },
            'memory': {
                'avg': sum(m.memory_percent for m in recent_metrics) / len(recent_metrics),
                'max': max(m.memory_percent for m in recent_metrics),
                'min': min(m.memory_percent for m in recent_metrics)
            },
            'response_time': {
                'avg': sum(m.avg_response_time for m in recent_metrics) / len(recent_metrics),
                'max': max(m.avg_response_time for m in recent_metrics),
                'min': min(m.avg_response_time for m in recent_metrics)
            },
            'cache_hit_rate': {
                'avg': sum(m.cache_hit_rate for m in recent_metrics) / len(recent_metrics),
                'max': max(m.cache_hit_rate for m in recent_metrics),
                'min': min(m.cache_hit_rate for m in recent_metrics)
            }
        }

# Middleware para tracking de performance
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    # Registrar métricas
    duration = time.time() - start_time
    performance_monitor.request_duration.observe(duration)
    performance_monitor.request_count.labels(
        method=request.method,
        endpoint=request.url.path
    ).inc()
    
    # Adicionar headers de performance
    response.headers["X-Response-Time"] = f"{duration:.3f}s"
    
    return response

# Endpoint para métricas
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")

# Endpoint para performance summary
@app.get("/performance/summary")
async def performance_summary(minutes: int = 5):
    summary = performance_monitor.get_performance_summary(minutes)
    return JSONResponse(content=summary)
```

## 🎯 Estratégia de Otimização

### 1. **Frontend Performance Targets**
- **First Contentful Paint**: < 1.2s
- **Largest Contentful Paint**: < 1.8s  
- **Time to Interactive**: < 1.5s
- **Bundle Size**: < 150KB
- **JavaScript Execution Time**: < 100ms

### 2. **Backend Performance Targets**
- **API Response Time**: < 200ms (p95)
- **Database Query Time**: < 50ms (p95)
- **Cache Hit Rate**: > 80%
- **CPU Usage**: < 70% (avg)
- **Memory Usage**: < 80% (avg)

### 3. **Database Performance Targets**
- **Query Time**: < 100ms (p95)
- **Connection Pool Usage**: < 80%
- **Index Usage**: > 95%
- **Table Scan Rate**: < 1%

## 🔧 Plano de Implementação Performance

### Sprint 1 (Crítico)
1. Otimizar App.jsx (particionar estado)
2. Implementar cache multi-layer
3. Adicionar índices database

### Sprint 2 (Alto)
1. Otimizar queries (resolver N+1)
2. Implementar code splitting
3. Adicionar monitoring básico

### Sprint 3 (Médio)
1. Implementar CDN
2. Otimizar bundle size
3. Adicionar performance alerts

## 🚀 Recomendações Finais

### Imediatas
- **Prioridade 1**: Otimização frontend
- **Prioridade 2**: Cache implementation
- **Investimento**: 40-60 horas

### Longo Prazo
- **Auto-scaling baseado em performance**
- **Predictive performance monitoring**
- **AI-powered optimization**

---

**Status**: 🟡 **Requer Atenção Crítica**  
**Prioridade**: Altíssima  
**Investimento Estimado**: 60-80 horas  
**ROI Esperado**: 5x (performance +用户体验)
