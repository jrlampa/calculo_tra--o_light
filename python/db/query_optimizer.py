"""
Database Query Optimizer for calculo_tração_light.
This module provides query optimization, indexing strategies, and performance monitoring.
"""

import logging
import time
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from contextlib import asynccontextmanager
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Metrics for a database query."""
    query_hash: str
    query_text: str
    execution_time: float
    execution_count: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    last_executed: float


class QueryOptimizer:
    """Database query optimizer and performance monitor."""
    
    def __init__(self):
        self.query_metrics: Dict[str, QueryMetrics] = {}
        self.slow_query_threshold = 1.0  # segundos
        self.index_suggestions = []
        self.lock = asyncio.Lock()
    
    async def track_query(self, query_text: str, execution_time: float):
        """Track query execution metrics."""
        query_hash = self._hash_query(query_text)
        
        async with self.lock:
            if query_hash in self.query_metrics:
                metrics = self.query_metrics[query_hash]
                metrics.execution_count += 1
                metrics.total_time += execution_time
                metrics.avg_time = metrics.total_time / metrics.execution_count
                metrics.min_time = min(metrics.min_time, execution_time)
                metrics.max_time = max(metrics.max_time, execution_time)
                metrics.last_executed = time.time()
            else:
                self.query_metrics[query_hash] = QueryMetrics(
                    query_hash=query_hash,
                    query_text=query_text,
                    execution_time=execution_time,
                    execution_count=1,
                    total_time=execution_time,
                    avg_time=execution_time,
                    min_time=execution_time,
                    max_time=execution_time,
                    last_executed=time.time()
                )
            
            # Check for slow queries
            if execution_time > self.slow_query_threshold:
                await self._analyze_slow_query(query_text, execution_time)
    
    def _hash_query(self, query_text: str) -> str:
        """Generate hash for query text."""
        import hashlib
        # Normalize query by removing extra whitespace and converting to lowercase
        normalized = ' '.join(query_text.split()).lower()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    async def _analyze_slow_query(self, query_text: str, execution_time: float):
        """Analyze slow queries and suggest optimizations."""
        logger.warning(f"Slow query detected: {execution_time:.4f}s - {query_text[:100]}...")
        
        # Analyze query pattern
        if 'SELECT' in query_text.upper():
            await self._suggest_indexes(query_text)
        
        if 'JOIN' in query_text.upper():
            await self._analyze_joins(query_text)
        
        if 'ORDER BY' in query_text.upper():
            await self._analyze_sorting(query_text)
    
    async def _suggest_indexes(self, query_text: str):
        """Suggest indexes for slow queries."""
        # Simple pattern matching for WHERE clauses
        import re
        
        # Extract table names
        table_pattern = r'FROM\s+(\w+)|JOIN\s+(\w+)'
        tables = re.findall(table_pattern, query_text, re.IGNORECASE)
        tables = [t for t in tables if t]
        
        # Extract WHERE conditions
        where_pattern = r'WHERE\s+(.*?)(?:\s+ORDER\s+BY|\s+GROUP\s+BY|\s+LIMIT|\s*$)'
        where_match = re.search(where_pattern, query_text, re.IGNORECASE | re.DOTALL)
        
        if where_match:
            where_clause = where_match.group(1)
            # Extract column names from WHERE clause
            column_pattern = r'(\w+)\s*[=<>!]'
            columns = re.findall(column_pattern, where_clause)
            
            for table in tables:
                for column in columns:
                    suggestion = f"CREATE INDEX idx_{table}_{column} ON {table} ({column});"
                    if suggestion not in self.index_suggestions:
                        self.index_suggestions.append(suggestion)
                        logger.info(f"Index suggestion: {suggestion}")
    
    async def _analyze_joins(self, query_text: str):
        """Analyze JOIN operations for potential issues."""
        import re
        
        # Count JOINs
        join_count = len(re.findall(r'\bJOIN\b', query_text, re.IGNORECASE))
        if join_count > 3:
            logger.warning(f"Query has {join_count} JOINs - consider query optimization")
        
        # Check for Cartesian products (JOINs without ON clauses)
        on_pattern = r'JOIN\s+\w+\s+(?!ON)'
        if re.search(on_pattern, query_text, re.IGNORECASE):
            logger.warning("Potential Cartesian product detected - missing ON clause")
    
    async def _analyze_sorting(self, query_text: str):
        """Analyze ORDER BY clauses."""
        import re
        
        # Check for ORDER BY without LIMIT
        order_pattern = r'ORDER\s+BY\s+.*?(?:(?!LIMIT).)*$'
        if re.search(order_pattern, query_text, re.IGNORECASE | re.DOTALL):
            if 'LIMIT' not in query_text.upper():
                logger.warning("ORDER BY without LIMIT may cause performance issues")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report."""
        if not self.query_metrics:
            return {"message": "No query metrics available"}
        
        # Calculate statistics
        execution_times = [metrics.execution_time for metrics in self.query_metrics.values()]
        
        report = {
            "total_queries": len(self.query_metrics),
            "total_executions": sum(metrics.execution_count for metrics in self.query_metrics.values()),
            "slow_queries": len([m for m in self.query_metrics.values() if m.execution_time > self.slow_query_threshold]),
            "avg_execution_time": statistics.mean(execution_times),
            "median_execution_time": statistics.median(execution_times),
            "max_execution_time": max(execution_times),
            "min_execution_time": min(execution_times),
            "index_suggestions": self.index_suggestions,
            "slowest_queries": self._get_slowest_queries(),
            "most_executed_queries": self._get_most_executed_queries()
        }
        
        return report
    
    def _get_slowest_queries(self) -> List[Dict[str, Any]]:
        """Get the slowest queries."""
        sorted_queries = sorted(self.query_metrics.values(), key=lambda x: x.execution_time, reverse=True)
        return [
            {
                "query": q.query_text[:200] + "..." if len(q.query_text) > 200 else q.query_text,
                "execution_time": q.execution_time,
                "execution_count": q.execution_count
            }
            for q in sorted_queries[:10]
        ]
    
    def _get_most_executed_queries(self) -> List[Dict[str, Any]]:
        """Get the most executed queries."""
        sorted_queries = sorted(self.query_metrics.values(), key=lambda x: x.execution_count, reverse=True)
        return [
            {
                "query": q.query_text[:200] + "..." if len(q.query_text) > 200 else q.query_text,
                "execution_count": q.execution_count,
                "total_time": q.total_time,
                "avg_time": q.avg_time
            }
            for q in sorted_queries[:10]
        ]


class ConnectionPoolOptimizer:
    """Optimize database connection pool settings."""
    
    def __init__(self, max_connections: int = 20, min_connections: int = 5):
        self.max_connections = max_connections
        self.min_connections = min_connections
        self.current_connections = 0
        self.connection_usage = []
        self.lock = asyncio.Lock()
    
    async def record_connection_usage(self, connection_count: int):
        """Record connection pool usage."""
        async with self.lock:
            self.current_connections = connection_count
            self.connection_usage.append({
                'timestamp': time.time(),
                'connections': connection_count
            })
            
            # Keep only last 1000 records
            if len(self.connection_usage) > 1000:
                self.connection_usage = self.connection_usage[-1000:]
    
    def get_optimal_pool_size(self) -> Dict[str, Any]:
        """Calculate optimal connection pool size."""
        if not self.connection_usage:
            return {
                "recommended_min": self.min_connections,
                "recommended_max": self.max_connections,
                "current_max": self.max_connections,
                "message": "Insufficient data for optimization"
            }
        
        # Calculate statistics
        connection_counts = [usage['connections'] for usage in self.connection_usage]
        
        avg_connections = statistics.mean(connection_counts)
        max_connections = max(connection_counts)
        p95_connections = self._calculate_percentile(connection_counts, 95)
        
        # Recommendations
        recommended_min = max(5, int(avg_connections * 0.8))
        recommended_max = max(20, int(p95_connections * 1.2))
        
        return {
            "recommended_min": recommended_min,
            "recommended_max": recommended_max,
            "current_max": self.max_connections,
            "avg_connections": avg_connections,
            "max_connections": max_connections,
            "p95_connections": p95_connections,
            "current_usage": self.current_connections
        }
    
    def _calculate_percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data."""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


class QueryCache:
    """Simple query result cache."""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl  # seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self.lock = asyncio.Lock()
    
    async def get(self, query_hash: str) -> Optional[Any]:
        """Get cached result."""
        async with self.lock:
            if query_hash in self.cache:
                # Check TTL
                if time.time() - self.access_times[query_hash] < self.ttl:
                    self.access_times[query_hash] = time.time()
                    logger.debug(f"Cache hit for query {query_hash}")
                    return self.cache[query_hash]['result']
                else:
                    # Expired
                    del self.cache[query_hash]
                    del self.access_times[query_hash]
            
            logger.debug(f"Cache miss for query {query_hash}")
            return None
    
    async def set(self, query_hash: str, result: Any):
        """Set cached result."""
        async with self.lock:
            # Eviction policy: remove oldest if cache is full
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
                del self.cache[oldest_key]
                del self.access_times[oldest_key]
            
            self.cache[query_hash] = {'result': result}
            self.access_times[query_hash] = time.time()
    
    def clear(self):
        """Clear cache."""
        self.cache.clear()
        self.access_times.clear()


# Global instances
query_optimizer = QueryOptimizer()
connection_optimizer = ConnectionPoolOptimizer()
query_cache = QueryCache()


@asynccontextmanager
async def track_query_performance(query_text: str):
    """Context manager to track query performance."""
    start_time = time.time()
    
    try:
        yield
    finally:
        execution_time = time.time() - start_time
        await query_optimizer.track_query(query_text, execution_time)


def optimize_query(query: str) -> str:
    """Apply basic query optimizations."""
    # Remove extra whitespace
    optimized = ' '.join(query.split())
    
    # Add query hints if needed
    if 'SELECT' in optimized.upper() and 'LIMIT' not in optimized.upper():
        # For SELECT queries without LIMIT, consider adding LIMIT for testing
        pass
    
    return optimized


async def get_performance_summary() -> Dict[str, Any]:
    """Get comprehensive performance summary."""
    query_report = query_optimizer.get_performance_report()
    pool_optimization = connection_optimizer.get_optimal_pool_size()
    
    return {
        "query_performance": query_report,
        "connection_pool": pool_optimization,
        "cache_stats": {
            "cache_size": len(query_cache.cache),
            "max_cache_size": query_cache.max_size,
            "ttl": query_cache.ttl
        }
    }