/* The above code is a React component called `CacheMonitor` that serves as a monitoring tool for a
cache system. Here is a summary of what the code is doing: */
import { Database, Activity, TrendingUp, AlertCircle, CheckCircle, Trash2, RefreshCw, BarChart3 } from 'lucide-react';
import React, { useState, useEffect } from 'react';

const CacheMonitor = () => {
  const [cacheStats, setCacheStats] = useState(null);
  const [cacheHealth, setCacheHealth] = useState(null);
  const [cacheKeys, setCacheKeys] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedKey, setSelectedKey] = useState(null);
  const [keyDetails, setKeyDetails] = useState(null);

  // Fetch cache statistics
  const fetchCacheStats = async () => {
    try {
      const response = await fetch('/api/cache/stats');
      const data = await response.json();
      
      if (response.ok) {
        setCacheStats(data);
        setError(null);
      } else {
        throw new Error(data.detail || 'Failed to fetch cache stats');
      }
    } catch (err) {
      setError(err.message);
      setCacheStats(null);
    }
  };

  // Fetch cache health
  const fetchCacheHealth = async () => {
    try {
      const response = await fetch('/api/cache/health');
      const data = await response.json();
      
      if (response.ok) {
        setCacheHealth(data);
      } else {
        throw new Error(data.detail || 'Failed to fetch cache health');
      }
    } catch (_err) {
      // no-op
    }
  };

  // Fetch cache keys
  const fetchCacheKeys = async (pattern = '*', prefix = 'default') => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/cache/keys?pattern=${pattern}&prefix=${prefix}&limit=50`);
      const data = await response.json();
      
      if (response.ok) {
        setCacheKeys(data.keys || []);
        setError(null);
      } else {
        throw new Error(data.detail || 'Failed to fetch cache keys');
      }
    } catch (err) {
      setError(err.message);
      setCacheKeys([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch key details
  const fetchKeyDetails = async (key, prefix = 'default') => {
    try {
      const response = await fetch(`/api/cache/key/${encodeURIComponent(key)}?prefix=${prefix}`);
      const data = await response.json();
      
      if (response.ok) {
        setKeyDetails(data);
      } else {
        throw new Error(data.detail || 'Failed to fetch key details');
      }
    } catch (err) {
      setError(err.message);
      setKeyDetails(null);
    }
  };

  // Clear cache
  const clearCache = async (pattern = null, prefix = 'default') => {
    try {
      const url = pattern 
        ? `/api/cache/clear?pattern=${pattern}&prefix=${prefix}`
        : '/api/cache/clear';
      
      const response = await fetch(url, { method: 'POST' });
      const data = await response.json();
      
      if (response.ok) {
        // Refresh data
        await fetchCacheStats();
        await fetchCacheKeys();
        await fetchCacheHealth();
        
        alert(data.message);
      } else {
        throw new Error(data.detail || 'Failed to clear cache');
      }
    } catch (err) {
      setError(err.message);
    }
  };

  // Delete specific key
  const deleteKey = async (key, prefix = 'default') => {
    try {
      const response = await fetch(`/api/cache/key/${encodeURIComponent(key)}?prefix=${prefix}`, {
        method: 'DELETE'
      });
      const data = await response.json();
      
      if (response.ok) {
        // Refresh data
        await fetchCacheStats();
        await fetchCacheKeys();
        setSelectedKey(null);
        setKeyDetails(null);
        
        alert(data.message);
      } else {
        throw new Error(data.detail || 'Failed to delete key');
      }
    } catch (err) {
      setError(err.message);
    }
  };

  // Get performance grade color
  const _getGradeColor = (grade) => {
    switch (grade) {
      case 'A': return 'text-green-600';
      case 'B': return 'text-blue-600';
      case 'C': return 'text-yellow-600';
      case 'D': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  // Initialize data
  useEffect(() => {
    fetchCacheStats();
    fetchCacheHealth();
    fetchCacheKeys();
    
    // Set up auto-refresh
    const interval = setInterval(() => {
      fetchCacheStats();
      fetchCacheHealth();
    }, 30000); // Refresh every 30 seconds
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-6 bg-white rounded-lg shadow-md">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold flex items-center">
          <Database className="w-6 h-6 mr-2 text-blue-600" />
          Cache Monitor
        </h2>
        <div className="flex space-x-2">
          <button
            onClick={() => {
              fetchCacheStats();
              fetchCacheHealth();
              fetchCacheKeys();
            }}
            className="flex items-center px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-1" />
            Refresh
          </button>
          <button
            onClick={() => clearCache()}
            className="flex items-center px-3 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
          >
            <Trash2 className="w-4 h-4 mr-1" />
            Clear All
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
            <span className="text-red-800 font-medium">Error</span>
          </div>
          <p className="text-red-600 text-sm mt-1">{error}</p>
        </div>
      )}

      {/* Cache Health */}
      {cacheHealth && (
        <div className="mb-6 p-4 border rounded-lg">
          <h3 className="text-lg font-semibold mb-3 flex items-center">
            {cacheHealth.status === 'healthy' ? (
              <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
            ) : (
              <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
            )}
            Cache Health: {cacheHealth.status}
          </h3>
          {cacheHealth.error && (
            <p className="text-red-600 text-sm">{cacheHealth.error}</p>
          )}
        </div>
      )}

      {/* Cache Statistics */}
      {cacheStats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="flex items-center justify-between">
              <Activity className="w-8 h-8 text-blue-600" />
              <span className="text-2xl font-bold text-blue-600">
                {cacheStats.hit_rate.toFixed(1)}%
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-2">Hit Rate</p>
          </div>

          <div className="bg-green-50 p-4 rounded-lg">
            <div className="flex items-center justify-between">
              <TrendingUp className="w-8 h-8 text-green-600" />
              <span className="text-2xl font-bold text-green-600">
                {cacheStats.local_stats.hits}
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-2">Cache Hits</p>
          </div>

          <div className="bg-yellow-50 p-4 rounded-lg">
            <div className="flex items-center justify-between">
              <BarChart3 className="w-8 h-8 text-yellow-600" />
              <span className="text-2xl font-bold text-yellow-600">
                {cacheStats.local_stats.misses}
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-2">Cache Misses</p>
          </div>

          <div className="bg-purple-50 p-4 rounded-lg">
            <div className="flex items-center justify-between">
              <Database className="w-8 h-8 text-purple-600" />
              <span className="text-2xl font-bold text-purple-600">
                {cacheStats.total_requests}
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-2">Total Requests</p>
          </div>
        </div>
      )}

      {/* Redis Info */}
      {cacheStats?.redis_info && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-lg font-semibold mb-3">Redis Information</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="font-medium">Memory:</span>
              <span className="ml-2">{cacheStats.redis_info.used_memory || 'N/A'}</span>
            </div>
            <div>
              <span className="font-medium">Clients:</span>
              <span className="ml-2">{cacheStats.redis_info.connected_clients || 'N/A'}</span>
            </div>
            <div>
              <span className="font-medium">Commands:</span>
              <span className="ml-2">{cacheStats.redis_info.total_commands_processed || 'N/A'}</span>
            </div>
            <div>
              <span className="font-medium">Keyspace Hits:</span>
              <span className="ml-2">{cacheStats.redis_info.keyspace_hits || 'N/A'}</span>
            </div>
          </div>
        </div>
      )}

      {/* Cache Keys */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <h3 className="text-lg font-semibold mb-3">Cache Keys</h3>
          
          {/* Key filters */}
          <div className="mb-4 flex space-x-2">
            <input
              type="text"
              placeholder="Pattern (e.g., projeto:*)"
              className="flex-1 px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  fetchCacheKeys(e.target.value, 'default');
                }
              }}
            />
            <select
              className="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              onChange={(e) => fetchCacheKeys('*', e.target.value)}
            >
              <option value="default">Default</option>
              <option value="projeto">Projeto</option>
              <option value="ponto">Ponto</option>
              <option value="calculo">Cálculo</option>
              <option value="user">User</option>
              <option value="session">Session</option>
              <option value="api">API</option>
            </select>
          </div>

          {/* Keys list */}
          <div className="border rounded-lg max-h-96 overflow-y-auto">
            {isLoading ? (
              <div className="p-4 text-center">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
                <p className="text-sm text-gray-600 mt-2">Loading keys...</p>
              </div>
            ) : cacheKeys.length > 0 ? (
              <div className="divide-y">
                {cacheKeys.map((keyInfo, index) => (
                  <div
                    key={index}
                    className={`p-3 hover:bg-gray-50 cursor-pointer ${
                      selectedKey === keyInfo.key ? 'bg-blue-50' : ''
                    }`}
                    onClick={() => {
                      setSelectedKey(keyInfo.key);
                      fetchKeyDetails(keyInfo.key, 'default');
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{keyInfo.key}</p>
                        <p className="text-xs text-gray-500">
                          TTL: {keyInfo.ttl}s | Type: {keyInfo.type}
                        </p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteKey(keyInfo.key, 'default');
                        }}
                        className="ml-2 text-red-600 hover:text-red-800"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 text-center text-gray-500">
                <Database className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                <p>No cache keys found</p>
              </div>
            )}
          </div>
        </div>

        {/* Key Details */}
        <div>
          <h3 className="text-lg font-semibold mb-3">Key Details</h3>
          
          {keyDetails ? (
            <div className="border rounded-lg p-4">
              <div className="mb-4">
                <h4 className="font-medium text-gray-700">Key</h4>
                <p className="text-sm text-gray-600 font-mono break-all">{keyDetails.key}</p>
              </div>
              
              <div className="mb-4">
                <h4 className="font-medium text-gray-700">Exists</h4>
                <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                  keyDetails.exists
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {keyDetails.exists ? 'Yes' : 'No'}
                </span>
              </div>
              
              <div className="mb-4">
                <h4 className="font-medium text-gray-700">TTL</h4>
                <p className="text-sm text-gray-600">
                  {keyDetails.ttl === -1 ? 'No expiration' : `${keyDetails.ttl} seconds`}
                </p>
              </div>
              
              {keyDetails.value && (
                <div className="mb-4">
                  <h4 className="font-medium text-gray-700">Value</h4>
                  <div className="bg-gray-50 p-3 rounded text-sm font-mono break-all max-h-48 overflow-y-auto">
                    {typeof keyDetails.value === 'object'
                      ? JSON.stringify(keyDetails.value, null, 2)
                      : String(keyDetails.value)}
                  </div>
                </div>
              )}
              
              <div className="text-xs text-gray-500">
                Last updated: {new Date(keyDetails.timestamp).toLocaleString()}
              </div>
            </div>
          ) : (
            <div className="border rounded-lg p-8 text-center text-gray-500">
              <Database className="w-12 h-12 mx-auto mb-2 text-gray-300" />
              <p>Select a key to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CacheMonitor;
