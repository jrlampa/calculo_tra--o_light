"""AI service for integration with calculation and project management."""
from __future__ import annotations

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ai.ollama_client import get_ai_assistant, ChatMessage
from models.projeto import Projeto, ProjetoCreate, ProjetoUpdate

logger = logging.getLogger(__name__)


class AIService:
    """AI service for intelligent assistance."""
    
    def __init__(self):
        self.ai_assistant = None
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure AI assistant is initialized."""
        if not self._initialized:
            self.ai_assistant = await get_ai_assistant()
            self._initialized = True
    
    async def analyze_calculation_results(self, calculation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze calculation results and provide insights."""
        await self._ensure_initialized()
        
        try:
            # Enhance calculation data with context
            enhanced_data = {
                "calculation_data": calculation_data,
                "analysis_request": "comprehensive_analysis",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Get AI analysis
            analysis = await self.ai_assistant.analyze_calculation(enhanced_data)
            
            # Parse and structure the analysis
            return {
                "status": "success",
                "analysis": analysis,
                "insights": self._parse_insights(analysis),
                "recommendations": self._parse_recommendations(analysis),
                "risks": self._parse_risks(analysis),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze calculation results: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def suggest_project_optimizations(self, projeto: Projeto) -> Dict[str, Any]:
        """Suggest optimizations for a project."""
        await self._ensure_initialized()
        
        try:
            # Prepare project data for AI
            project_data = {
                "project_id": str(projeto.id) if hasattr(projeto, 'id') else "unknown",
                "name": getattr(projeto, 'nome', 'Unknown'),
                "organization": getattr(projeto, 'orgao', 'Unknown'),
                "study_date": getattr(projeto, 'data_estudo', None),
                "description": getattr(projeto, 'descricao', ''),
                "project_type": "cálculo_de_tração",
                "optimization_goals": ["cost_reduction", "safety_improvement", "efficiency"]
            }
            
            # Get AI suggestions
            suggestions = await self.ai_assistant.suggest_optimization(project_data)
            
            return {
                "status": "success",
                "suggestions": suggestions,
                "project_id": project_data["project_id"],
                "optimization_areas": self._parse_optimization_areas(suggestions),
                "estimated_savings": self._parse_savings(suggestions),
                "implementation_priority": self._parse_priority(suggestions),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to suggest project optimizations: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def validate_calculation_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate calculation parameters with AI."""
        await self._ensure_initialized()
        
        try:
            # Prepare validation prompt
            validation_prompt = f"""Valide os seguintes parâmetros de cálculo de tração:

{json.dumps(parameters, indent=2, ensure_ascii=False)}

Verifique:
1. Consistência dos valores
2. Conformidade com normas técnicas
3. Possíveis erros de digitação
4. Valores fora de faixa esperada
5. Unidades de medida corretas

Retorne uma análise detalhada da validação."""
            
            # Get AI validation
            validation = await self.ai_assistant.chat(validation_prompt)
            
            return {
                "status": "success",
                "validation": validation,
                "is_valid": self._parse_validation_result(validation),
                "issues_found": self._parse_validation_issues(validation),
                "recommendations": self._parse_validation_recommendations(validation),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to validate calculation parameters: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def generate_technical_report(self, calculation_data: Dict[str, Any], project_info: Dict[str, Any]) -> str:
        """Generate technical report with AI."""
        await self._ensure_initialized()
        
        try:
            # Prepare report generation prompt
            report_prompt = f"""Gere um relatório técnico completo com base nos seguintes dados:

DADOS DO PROJETO:
{json.dumps(project_info, indent=2, ensure_ascii=False)}

DADOS DO CÁLCULO:
{json.dumps(calculation_data, indent=2, ensure_ascii=False)}

O relatório deve incluir:
1. Sumário executivo
2. Descrição do projeto
3. Metodologia de cálculo
4. Resultados obtidos
5. Análise de resultados
6. Conclusões e recomendações
7. Análise de conformidade técnica

Use linguagem técnica profissional e formato estruturado."""
            
            # Generate report
            report = await self.ai_assistant.chat(report_prompt)
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate technical report: {e}")
            raise
    
    async def chat_with_context(self, message: str, context: Dict[str, Any], conversation_id: Optional[str] = None) -> str:
        """Chat with AI using specific context."""
        await self._ensure_initialized()
        
        try:
            # Prepare context-aware prompt
            context_prompt = f"""Contexto atual do projeto/cálculo:

{json.dumps(context, indent=2, ensure_ascii=False)}

Com base neste contexto, responda à seguinte pergunta:
{message}

Seja específico e técnico, considerando os dados fornecidos."""
            
            # Get conversation history if provided
            history = []
            if conversation_id:
                from api.routers.ai_assistant import conversations
                history = conversations.get(conversation_id, [])
            
            # Chat with context
            response = await self.ai_assistant.chat(context_prompt, history)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to chat with context: {e}")
            raise
    
    def _parse_insights(self, analysis: str) -> List[str]:
        """Parse insights from AI analysis."""
        # Simple parsing - in production, use more sophisticated NLP
        insights = []
        lines = analysis.split('\n')
        
        for line in lines:
            if 'insight:' in line.lower() or 'observação:' in line.lower():
                insights.append(line.strip())
        
        return insights[:5]  # Limit to 5 insights
    
    def _parse_recommendations(self, analysis: str) -> List[str]:
        """Parse recommendations from AI analysis."""
        recommendations = []
        lines = analysis.split('\n')
        
        for line in lines:
            if 'recommendation:' in line.lower() or 'recomendação:' in line.lower():
                recommendations.append(line.strip())
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _parse_risks(self, analysis: str) -> List[str]:
        """Parse risks from AI analysis."""
        risks = []
        lines = analysis.split('\n')
        
        for line in lines:
            if 'risk:' in line.lower() or 'risco:' in line.lower():
                risks.append(line.strip())
        
        return risks[:5]  # Limit to 5 risks
    
    def _parse_optimization_areas(self, suggestions: str) -> List[str]:
        """Parse optimization areas from suggestions."""
        areas = []
        lines = suggestions.split('\n')
        
        for line in lines:
            if 'area:' in line.lower() or 'área:' in line.lower():
                areas.append(line.strip())
        
        return areas[:5]  # Limit to 5 areas
    
    def _parse_savings(self, suggestions: str) -> Dict[str, str]:
        """Parse potential savings from suggestions."""
        savings = {}
        lines = suggestions.split('\n')
        
        for line in lines:
            if 'saving:' in line.lower() or 'economia:' in line.lower():
                parts = line.split(':')
                if len(parts) > 1:
                    key = parts[0].strip()
                    value = ':'.join(parts[1:]).strip()
                    savings[key] = value
        
        return savings
    
    def _parse_priority(self, suggestions: str) -> List[Dict[str, str]]:
        """Parse implementation priority from suggestions."""
        priorities = []
        lines = suggestions.split('\n')
        
        for line in lines:
            if 'priority:' in line.lower() or 'prioridade:' in line.lower():
                parts = line.split(':')
                if len(parts) > 1:
                    priority = parts[0].strip()
                    description = ':'.join(parts[1:]).strip()
                    priorities.append({
                        "priority": priority,
                        "description": description
                    })
        
        return priorities[:5]  # Limit to 5 priorities
    
    def _parse_validation_result(self, validation: str) -> bool:
        """Parse validation result."""
        validation_lower = validation.lower()
        
        # Look for validation keywords
        if 'válido' in validation_lower and 'inválido' not in validation_lower:
            return True
        elif 'inválido' in validation_lower or 'erro' in validation_lower:
            return False
        elif 'problema' in validation_lower or 'issue' in validation_lower:
            return False
        
        return True  # Default to valid if unclear
    
    def _parse_validation_issues(self, validation: str) -> List[str]:
        """Parse validation issues."""
        issues = []
        lines = validation.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['erro:', 'error:', 'problema:', 'issue:', 'inválido:', 'invalid:']):
                issues.append(line.strip())
        
        return issues[:5]  # Limit to 5 issues
    
    def _parse_validation_recommendations(self, validation: str) -> List[str]:
        """Parse validation recommendations."""
        recommendations = []
        lines = validation.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['recomendação:', 'recommendation:', 'sugestão:', 'suggestion:']):
                recommendations.append(line.strip())
        
        return recommendations[:5]  # Limit to 5 recommendations


# Global AI service instance
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Get AI service instance."""
    global _ai_service
    
    if _ai_service is None:
        _ai_service = AIService()
    
    return _ai_service
