/* The above code is a React component named `AIAssistant` that serves as an AI chatbot interface. Here
is a summary of its functionality: */
import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Trash2, MessageSquare, TrendingUp, AlertTriangle } from 'lucide-react';

const AIAssistant = ({ calculationData, projectData, onOptimizationSuggestion }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [aiStatus, setAiStatus] = useState({ connected: false, model: null });
  const [activeTab, setActiveTab] = useState('chat');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [optimizationResult, setOptimizationResult] = useState(null);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Check AI status on mount
  useEffect(() => {
    checkAIStatus();
  }, []);

  const checkAIStatus = async () => {
    try {
      const response = await fetch('/api/ai/status');
      const data = await response.json();
      setAiStatus({
        connected: data.ollama_connected,
        model: data.current_model
      });
    } catch (error) {
      console.error('Failed to check AI status:', error);
      setAiStatus({ connected: false, model: null });
    }
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputValue.trim(),
          conversation_id: conversationId,
          stream: false
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        const aiMessage = {
          role: 'assistant',
          content: data.response,
          timestamp: data.timestamp
        };

        setMessages(prev => [...prev, aiMessage]);
        setConversationId(data.conversation_id);
      } else {
        throw new Error(data.detail || 'Failed to send message');
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.',
        timestamp: new Date().toISOString(),
        isError: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const analyzeCalculation = async () => {
    if (!calculationData) return;

    setIsLoading(true);
    setActiveTab('analysis');

    try {
      const response = await fetch('/api/ai/analyze/calculation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          calculation_data: calculationData,
          analysis_type: 'comprehensive'
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        setAnalysisResult(data);
      } else {
        throw new Error(data.detail || 'Failed to analyze calculation');
      }
    } catch (error) {
      console.error('Failed to analyze calculation:', error);
      setAnalysisResult({
        status: 'error',
        error: error.message,
        analysis: 'Não foi possível analisar os dados do cálculo.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const optimizeProject = async () => {
    if (!projectData) return;

    setIsLoading(true);
    setActiveTab('optimization');

    try {
      const response = await fetch('/api/ai/optimize/project', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_data: projectData,
          optimization_goals: ['cost_reduction', 'safety_improvement', 'efficiency']
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        setOptimizationResult(data);
        if (onOptimizationSuggestion) {
          onOptimizationSuggestion(data.suggestions);
        }
      } else {
        throw new Error(data.detail || 'Failed to optimize project');
      }
    } catch (error) {
      console.error('Failed to optimize project:', error);
      setOptimizationResult({
        status: 'error',
        error: error.message,
        suggestions: 'Não foi possível gerar sugestões de otimização.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const clearConversation = async () => {
    if (conversationId) {
      try {
        await fetch(`/api/ai/conversations/${conversationId}`, {
          method: 'DELETE'
        });
      } catch (error) {
        console.error('Failed to clear conversation:', error);
      }
    }
    
    setMessages([]);
    setConversationId(null);
    setAnalysisResult(null);
    setOptimizationResult(null);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (!isOpen) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={() => setIsOpen(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white rounded-full p-4 shadow-lg transition-all duration-200 hover:scale-105"
          title="Assistente IA"
        >
          <Bot className="w-6 h-6" />
        </button>
        {!aiStatus.connected && (
          <div className="absolute -top-2 -right-2 bg-red-500 rounded-full w-3 h-3 animate-pulse" />
        )}
      </div>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 w-96 h-[600px] bg-white rounded-lg shadow-2xl border border-gray-200 flex flex-col">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 rounded-t-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Bot className="w-5 h-5" />
            <h3 className="font-semibold">Assistente IA</h3>
            {aiStatus.model && (
              <span className="text-xs bg-white/20 px-2 py-1 rounded">
                {aiStatus.model}
              </span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={clearConversation}
              className="text-white/80 hover:text-white transition-colors"
              title="Limpar conversa"
            >
              <Trash2 className="w-4 h-4" />
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="text-white/80 hover:text-white transition-colors"
            >
              ×
            </button>
          </div>
        </div>
        
        {/* Status indicator */}
        <div className="flex items-center space-x-2 mt-2">
          <div className={`w-2 h-2 rounded-full ${aiStatus.connected ? 'bg-green-400' : 'bg-red-400'}`} />
          <span className="text-xs">
            {aiStatus.connected ? 'Conectado' : 'Desconectado'}
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200">
        <button
          onClick={() => setActiveTab('chat')}
          className={`flex-1 py-2 px-4 text-sm font-medium transition-colors ${
            activeTab === 'chat'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          <MessageSquare className="w-4 h-4 inline mr-1" />
          Chat
        </button>
        <button
          onClick={analyzeCalculation}
          disabled={!calculationData || isLoading}
          className={`flex-1 py-2 px-4 text-sm font-medium transition-colors ${
            activeTab === 'analysis'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-gray-600 hover:text-gray-800 disabled:opacity-50'
          }`}
        >
          <TrendingUp className="w-4 h-4 inline mr-1" />
          Análise
        </button>
        <button
          onClick={optimizeProject}
          disabled={!projectData || isLoading}
          className={`flex-1 py-2 px-4 text-sm font-medium transition-colors ${
            activeTab === 'optimization'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-gray-600 hover:text-gray-800 disabled:opacity-50'
          }`}
        >
          <AlertTriangle className="w-4 h-4 inline mr-1" />
          Otimizar
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'chat' && (
          <div className="h-full flex flex-col">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.length === 0 && (
                <div className="text-center text-gray-500 py-8">
                  <Bot className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                  <p>Olá! Sou seu assistente de IA especializado em cálculo de tração.</p>
                  <p className="text-sm mt-1">Como posso ajudar você hoje?</p>
                </div>
              )}
              
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-3 ${
                      message.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : message.isError
                        ? 'bg-red-100 text-red-800 border border-red-200'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    <div className="flex items-start space-x-2">
                      {message.role === 'user' ? (
                        <User className="w-4 h-4 mt-0.5 flex-shrink-0" />
                      ) : (
                        <Bot className="w-4 h-4 mt-0.5 flex-shrink-0" />
                      )}
                      <div className="flex-1">
                        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                        <p className="text-xs opacity-70 mt-1">
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-lg p-3">
                    <div className="flex items-center space-x-2">
                      <Bot className="w-4 h-4" />
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="border-t border-gray-200 p-4">
              <div className="flex space-x-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Digite sua mensagem..."
                  disabled={isLoading || !aiStatus.connected}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                />
                <button
                  onClick={sendMessage}
                  disabled={isLoading || !inputValue.trim() || !aiStatus.connected}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg px-4 py-2 transition-colors disabled:cursor-not-allowed"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'analysis' && (
          <div className="h-full overflow-y-auto p-4">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-2">Analisando dados...</span>
              </div>
            ) : analysisResult ? (
              <div className="space-y-4">
                {analysisResult.status === 'error' ? (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <h4 className="text-red-800 font-medium">Erro na análise</h4>
                    <p className="text-red-600 text-sm mt-1">{analysisResult.error}</p>
                  </div>
                ) : (
                  <>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <h4 className="text-blue-800 font-medium">Análise Completa</h4>
                      <div className="mt-2 text-sm text-gray-700 whitespace-pre-wrap">
                        {analysisResult.analysis}
                      </div>
                    </div>
                    
                    {analysisResult.insights && analysisResult.insights.length > 0 && (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <h4 className="text-green-800 font-medium">Insights</h4>
                        <ul className="mt-2 text-sm text-gray-700 space-y-1">
                          {analysisResult.insights.map((insight, index) => (
                            <li key={index} className="flex items-start">
                              <span className="text-green-600 mr-2">•</span>
                              {insight}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {analysisResult.recommendations && analysisResult.recommendations.length > 0 && (
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <h4 className="text-yellow-800 font-medium">Recomendações</h4>
                        <ul className="mt-2 text-sm text-gray-700 space-y-1">
                          {analysisResult.recommendations.map((rec, index) => (
                            <li key={index} className="flex items-start">
                              <span className="text-yellow-600 mr-2">•</span>
                              {rec}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </>
                )}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <TrendingUp className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                <p> clique em "Análise" para analisar os dados do cálculo</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'optimization' && (
          <div className="h-full overflow-y-auto p-4">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-2">Gerando sugestões...</span>
              </div>
            ) : optimizationResult ? (
              <div className="space-y-4">
                {optimizationResult.status === 'error' ? (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <h4 className="text-red-800 font-medium">Erro na otimização</h4>
                    <p className="text-red-600 text-sm mt-1">{optimizationResult.error}</p>
                  </div>
                ) : (
                  <>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <h4 className="text-blue-800 font-medium">Sugestões de Otimização</h4>
                      <div className="mt-2 text-sm text-gray-700 whitespace-pre-wrap">
                        {optimizationResult.suggestions}
                      </div>
                    </div>
                    
                    {optimizationResult.optimization_areas && optimizationResult.optimization_areas.length > 0 && (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <h4 className="text-green-800 font-medium">Áreas de Otimização</h4>
                        <ul className="mt-2 text-sm text-gray-700 space-y-1">
                          {optimizationResult.optimization_areas.map((area, index) => (
                            <li key={index} className="flex items-start">
                              <span className="text-green-600 mr-2">•</span>
                              {area}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {optimizationResult.estimated_savings && Object.keys(optimizationResult.estimated_savings).length > 0 && (
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <h4 className="text-yellow-800 font-medium">Economias Estimadas</h4>
                        <div className="mt-2 text-sm text-gray-700 space-y-1">
                          {Object.entries(optimizationResult.estimated_savings).map(([key, value]) => (
                            <div key={key} className="flex justify-between">
                              <span>{key}:</span>
                              <span className="font-medium">{value}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <AlertTriangle className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                <p>Clique em "Otimizar" para gerar sugestões de otimização</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AIAssistant;
