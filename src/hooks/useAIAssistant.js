import { useState, useEffect, useCallback } from 'react';

export const useAIAssistant = () => {
  const [aiStatus, setAiStatus] = useState({
    connected: false,
    model: null,
    loading: true
  });
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Check AI status
  const checkAIStatus = useCallback(async () => {
    try {
      setAiStatus(prev => ({ ...prev, loading: true }));
      
      const response = await fetch('/api/ai/status');
      const data = await response.json();
      
      setAiStatus({
        connected: data.ollama_connected,
        model: data.current_model,
        loading: false
      });
    } catch (error) {
      console.error('Failed to check AI status:', error);
      setAiStatus({
        connected: false,
        model: null,
        loading: false
      });
    }
  }, []);

  // Load conversations
  const loadConversations = useCallback(async () => {
    try {
      const response = await fetch('/api/ai/conversations');
      const data = await response.json();
      
      if (response.ok) {
        setConversations(data.conversations || []);
      }
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  }, []);

  // Send message to AI
  const sendMessage = useCallback(async (message, conversationId = null) => {
    if (!aiStatus.connected) {
      throw new Error('AI Assistant is not connected');
    }

    setIsProcessing(true);

    try {
      const response = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          conversation_id: conversationId,
          stream: false
        })
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to send message');
      }

      return {
        response: data.response,
        conversationId: data.conversation_id,
        model: data.model,
        timestamp: data.timestamp
      };
    } catch (error) {
      console.error('Failed to send message:', error);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, [aiStatus.connected]);

  // Stream chat with AI
  const streamMessage = useCallback(async (message, conversationId = null, onChunk = null) => {
    if (!aiStatus.connected) {
      throw new Error('AI Assistant is not connected');
    }

    setIsProcessing(true);

    try {
      const response = await fetch('/api/ai/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          conversation_id: conversationId,
          stream: true
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to stream message');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullResponse = '';
      let responseConversationId = conversationId;

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.chunk) {
                fullResponse += data.chunk;
                responseConversationId = data.conversation_id;
                
                if (onChunk) {
                  onChunk(data.chunk, data.conversation_id);
                }
              }
              
              if (data.done) {
                return {
                  response: fullResponse,
                  conversationId: responseConversationId,
                  done: true
                };
              }
              
              if (data.error) {
                throw new Error(data.error);
              }
            } catch (e) {
              // Ignore parsing errors for partial chunks
              continue;
            }
          }
        }
      }

      return {
        response: fullResponse,
        conversationId: responseConversationId,
        done: true
      };
    } catch (error) {
      console.error('Failed to stream message:', error);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, [aiStatus.connected]);

  // Analyze calculation
  const analyzeCalculation = useCallback(async (calculationData, analysisType = 'general') => {
    if (!aiStatus.connected) {
      throw new Error('AI Assistant is not connected');
    }

    setIsProcessing(true);

    try {
      const response = await fetch('/api/ai/analyze/calculation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          calculation_data: calculationData,
          analysis_type: analysisType
        })
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to analyze calculation');
      }

      return data;
    } catch (error) {
      console.error('Failed to analyze calculation:', error);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, [aiStatus.connected]);

  // Optimize project
  const optimizeProject = useCallback(async (projectData, optimizationGoals = ['cost', 'performance']) => {
    if (!aiStatus.connected) {
      throw new Error('AI Assistant is not connected');
    }

    setIsProcessing(true);

    try {
      const response = await fetch('/api/ai/optimize/project', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_data: projectData,
          optimization_goals: optimizationGoals
        })
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to optimize project');
      }

      return data;
    } catch (error) {
      console.error('Failed to optimize project:', error);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, [aiStatus.connected]);

  // Get conversation history
  const getConversation = useCallback(async (conversationId) => {
    try {
      const response = await fetch(`/api/ai/conversations/${conversationId}`);
      const data = await response.json();
      
      if (response.ok) {
        return data.messages;
      } else {
        throw new Error(data.detail || 'Failed to get conversation');
      }
    } catch (error) {
      console.error('Failed to get conversation:', error);
      throw error;
    }
  }, []);

  // Delete conversation
  const deleteConversation = useCallback(async (conversationId) => {
    try {
      const response = await fetch(`/api/ai/conversations/${conversationId}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete conversation');
      }

      // Update local state
      setConversations(prev => prev.filter(conv => conv.conversation_id !== conversationId));
      
      if (activeConversation === conversationId) {
        setActiveConversation(null);
      }

      return true;
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      throw error;
    }
  }, [activeConversation]);

  // Generate technical report
  const generateTechnicalReport = useCallback(async (calculationData, projectInfo) => {
    if (!aiStatus.connected) {
      throw new Error('AI Assistant is not connected');
    }

    setIsProcessing(true);

    try {
      // This would need to be implemented in the backend
      // For now, we'll use the regular chat with a specific prompt
      const prompt = `Gere um relatório técnico completo com base nos seguintes dados:

DADOS DO PROJETO:
${JSON.stringify(projectInfo, null, 2)}

DADOS DO CÁLCULO:
${JSON.stringify(calculationData, null, 2)}

O relatório deve incluir:
1. Sumário executivo
2. Descrição do projeto
3. Metodologia de cálculo
4. Resultados obtidos
5. Análise de resultados
6. Conclusões e recomendações
7. Análise de conformidade técnica

Use linguagem técnica profissional e formato estruturado.`;

      const result = await sendMessage(prompt);
      return result.response;
    } catch (error) {
      console.error('Failed to generate technical report:', error);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, [aiStatus.connected, sendMessage]);

  // Validate parameters
  const validateParameters = useCallback(async (parameters) => {
    if (!aiStatus.connected) {
      throw new Error('AI Assistant is not connected');
    }

    setIsProcessing(true);

    try {
      // This would need to be implemented in the backend
      // For now, we'll use the regular chat with a specific prompt
      const prompt = `Valide os seguintes parâmetros de cálculo de tração:

${JSON.stringify(parameters, null, 2)}

Verifique:
1. Consistência dos valores
2. Conformidade com normas técnicas
3. Possíveis erros de digitação
4. Valores fora de faixa esperada
5. Unidades de medida corretas

Retorne uma análise detalhada da validação.`;

      const result = await sendMessage(prompt);
      return result.response;
    } catch (error) {
      console.error('Failed to validate parameters:', error);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, [aiStatus.connected, sendMessage]);

  // Initialize on mount
  useEffect(() => {
    checkAIStatus();
    loadConversations();
  }, [checkAIStatus, loadConversations]);

  // Auto-refresh status periodically
  useEffect(() => {
    const interval = setInterval(() => {
      checkAIStatus();
    }, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, [checkAIStatus]);

  return {
    // Status
    aiStatus,
    isProcessing,
    conversations,
    activeConversation,
    
    // Actions
    checkAIStatus,
    loadConversations,
    sendMessage,
    streamMessage,
    analyzeCalculation,
    optimizeProject,
    getConversation,
    deleteConversation,
    generateTechnicalReport,
    validateParameters,
    
    // State setters
    setActiveConversation,
    setConversations
  };
};
