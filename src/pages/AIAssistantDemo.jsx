/**
 * The AIAssistantDemo component in this code snippet demonstrates the use of an AI assistant for
 * calculating traction in electrical networks.
 * @returns The `AIAssistantDemo` component is being returned. This component contains various sections
 * including header, status card, demo actions buttons for analyzing calculation, optimizing project,
 * generating report, and validating parameters. It also displays loading indicators, results grid for
 * analysis, optimization, report, and validation results. Additionally, it includes demo data for
 * calculation and project details.
 */
import { Bot, Cpu, Database, Zap, TrendingUp, CheckCircle, XCircle } from 'lucide-react';
import React, { useState } from 'react';

import { useAIAssistant } from '../hooks/useAIAssistant';

const AIAssistantDemo = () => {
  const {
    aiStatus,
    isProcessing,
    analyzeCalculation,
    optimizeProject,
    generateTechnicalReport,
    validateParameters
  } = useAIAssistant();

  const [_demoData, _setDemoData] = useState({
    calculation: {
      poste: {
        altura: 12,
        material: "concreto",
        bitola: 12
      },
      cabos: [
        {
          tipo: "CA",
          bitola: 50,
          tensao: 13800,
          flecha: 2.5
        }
      ],
      resultados: {
        tracao_maxima: 850,
        seguranca: 2.1,
        deformacao: 15
      }
    },
    project: {
      nome: "Projeto Teste",
      orgao: "Eletropaulo",
      local: "São Paulo - SP",
      descricao: "Projeto de rede de distribuição urbana",
      orcamento: 150000
    }
  });

  const [analysisResult, setAnalysisResult] = useState(null);
  const [optimizationResult, setOptimizationResult] = useState(null);
  const [reportResult, setReportResult] = useState(null);
  const [validationResult, setValidationResult] = useState(null);

  const handleAnalyzeCalculation = async () => {
    try {
      const result = await analyzeCalculation(demoData.calculation, 'comprehensive');
      setAnalysisResult(result);
    } catch (error) {
      setAnalysisResult({
        status: 'error',
        error: error.message
      });
    }
  };

  const handleOptimizeProject = async () => {
    try {
      const result = await optimizeProject(demoData.project, ['cost_reduction', 'safety_improvement', 'efficiency']);
      setOptimizationResult(result);
    } catch (error) {
      setOptimizationResult({
        status: 'error',
        error: error.message
      });
    }
  };

  const handleGenerateReport = async () => {
    try {
      const report = await generateTechnicalReport(demoData.calculation, demoData.project);
      setReportResult({
        status: 'success',
        report
      });
    } catch (error) {
      setReportResult({
        status: 'error',
        error: error.message
      });
    }
  };

  const handleValidateParameters = async () => {
    try {
      const validation = await validateParameters(demoData.calculation);
      setValidationResult({
        status: 'success',
        validation
      });
    } catch (error) {
      setValidationResult({
        status: 'error',
        error: error.message
      });
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center justify-center">
            <Bot className="w-8 h-8 mr-3 text-blue-600" />
            AI Assistant Demo
          </h1>
          <p className="mt-2 text-gray-600">
            Demonstração do assistente de IA para cálculo de tração de redes elétricas
          </p>
        </div>

        {/* Status Card */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${aiStatus.connected ? 'bg-green-500' : 'bg-red-500'}`} />
              <h2 className="text-lg font-semibold">Status do AI Assistant</h2>
            </div>
            <div className="text-sm text-gray-600">
              {aiStatus.loading ? 'Verificando...' : aiStatus.connected ? 'Conectado' : 'Desconectado'}
            </div>
          </div>
          
          {aiStatus.model && (
            <div className="mt-4 flex items-center space-x-2">
              <Cpu className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-600">Modelo: {aiStatus.model}</span>
            </div>
          )}
          
          {!aiStatus.connected && (
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">
                <strong>Atenção:</strong> O AI Assistant não está conectado. 
                Verifique se o Ollama está rodando em localhost:11434.
              </p>
            </div>
          )}
        </div>

        {/* Demo Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <button
            onClick={handleAnalyzeCalculation}
            disabled={!aiStatus.connected || isProcessing}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg p-4 transition-colors disabled:cursor-not-allowed"
          >
            <div className="flex flex-col items-center">
              <TrendingUp className="w-6 h-6 mb-2" />
              <span className="text-sm font-medium">Analisar Cálculo</span>
            </div>
          </button>

          <button
            onClick={handleOptimizeProject}
            disabled={!aiStatus.connected || isProcessing}
            className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg p-4 transition-colors disabled:cursor-not-allowed"
          >
            <div className="flex flex-col items-center">
              <Zap className="w-6 h-6 mb-2" />
              <span className="text-sm font-medium">Otimizar Projeto</span>
            </div>
          </button>

          <button
            onClick={handleGenerateReport}
            disabled={!aiStatus.connected || isProcessing}
            className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white rounded-lg p-4 transition-colors disabled:cursor-not-allowed"
          >
            <div className="flex flex-col items-center">
              <Database className="w-6 h-6 mb-2" />
              <span className="text-sm font-medium">Gerar Relatório</span>
            </div>
          </button>

          <button
            onClick={handleValidateParameters}
            disabled={!aiStatus.connected || isProcessing}
            className="bg-orange-600 hover:bg-orange-700 disabled:bg-gray-400 text-white rounded-lg p-4 transition-colors disabled:cursor-not-allowed"
          >
            <div className="flex flex-col items-center">
              <CheckCircle className="w-6 h-6 mb-2" />
              <span className="text-sm font-medium">Validar Parâmetros</span>
            </div>
          </button>
        </div>

        {/* Loading Indicator */}
        {isProcessing && (
          <div className="text-center mb-8">
            <div className="inline-flex items-center space-x-2">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              <span className="text-gray-600">Processando...</span>
            </div>
          </div>
        )}

        {/* Results Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Analysis Result */}
          {analysisResult && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <TrendingUp className="w-5 h-5 mr-2 text-blue-600" />
                Análise do Cálculo
              </h3>
              
              {analysisResult.status === 'error' ? (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <XCircle className="w-5 h-5 text-red-600 mr-2" />
                    <span className="text-red-800 font-medium">Erro</span>
                  </div>
                  <p className="text-red-600 text-sm mt-1">{analysisResult.error}</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 className="text-blue-800 font-medium mb-2">Análise Completa</h4>
                    <div className="text-sm text-gray-700 whitespace-pre-wrap">
                      {analysisResult.analysis}
                    </div>
                  </div>
                  
                  {analysisResult.insights && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <h4 className="text-green-800 font-medium mb-2">Insights</h4>
                      <ul className="text-sm text-gray-700 space-y-1">
                        {analysisResult.insights.map((insight, index) => (
                          <li key={index} className="flex items-start">
                            <span className="text-green-600 mr-2">•</span>
                            {insight}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Optimization Result */}
          {optimizationResult && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <Zap className="w-5 h-5 mr-2 text-green-600" />
                Otimização do Projeto
              </h3>
              
              {optimizationResult.status === 'error' ? (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <XCircle className="w-5 h-5 text-red-600 mr-2" />
                    <span className="text-red-800 font-medium">Erro</span>
                  </div>
                  <p className="text-red-600 text-sm mt-1">{optimizationResult.error}</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <h4 className="text-green-800 font-medium mb-2">Sugestões de Otimização</h4>
                    <div className="text-sm text-gray-700 whitespace-pre-wrap">
                      {optimizationResult.suggestions}
                    </div>
                  </div>
                  
                  {optimizationResult.optimization_areas && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <h4 className="text-blue-800 font-medium mb-2">Áreas de Otimização</h4>
                      <ul className="text-sm text-gray-700 space-y-1">
                        {optimizationResult.optimization_areas.map((area, index) => (
                          <li key={index} className="flex items-start">
                            <span className="text-blue-600 mr-2">•</span>
                            {area}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Report Result */}
          {reportResult && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <Database className="w-5 h-5 mr-2 text-purple-600" />
                Relatório Técnico
              </h3>
              
              {reportResult.status === 'error' ? (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <XCircle className="w-5 h-5 text-red-600 mr-2" />
                    <span className="text-red-800 font-medium">Erro</span>
                  </div>
                  <p className="text-red-600 text-sm mt-1">{reportResult.error}</p>
                </div>
              ) : (
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <h4 className="text-purple-800 font-medium mb-2">Relatório Gerado</h4>
                  <div className="text-sm text-gray-700 whitespace-pre-wrap max-h-96 overflow-y-auto">
                    {reportResult.report}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Validation Result */}
          {validationResult && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <CheckCircle className="w-5 h-5 mr-2 text-orange-600" />
                Validação de Parâmetros
              </h3>
              
              {validationResult.status === 'error' ? (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <XCircle className="w-5 h-5 text-red-600 mr-2" />
                    <span className="text-red-800 font-medium">Erro</span>
                  </div>
                  <p className="text-red-600 text-sm mt-1">{validationResult.error}</p>
                </div>
              ) : (
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                  <h4 className="text-orange-800 font-medium mb-2">Resultado da Validação</h4>
                  <div className="text-sm text-gray-700 whitespace-pre-wrap">
                    {validationResult.validation}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Demo Data */}
        <div className="mt-8 bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Dados de Demonstração</h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-700 mb-2">Dados do Cálculo</h4>
              <pre className="text-xs bg-gray-50 p-3 rounded overflow-x-auto">
                {JSON.stringify(demoData.calculation, null, 2)}
              </pre>
            </div>
            <div>
              <h4 className="font-medium text-gray-700 mb-2">Dados do Projeto</h4>
              <pre className="text-xs bg-gray-50 p-3 rounded overflow-x-auto">
                {JSON.stringify(demoData.project, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIAssistantDemo;
