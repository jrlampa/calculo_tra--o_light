"""Ollama client for AI assistant integration."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import UTC, datetime

# import aiohttp (DISABLED: Host dependency issues)
from pydantic import BaseModel, Field

from core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class AIModel:
    """AI model configuration."""
    name: str
    size: str
    modified: datetime
    digest: str


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Message role: user, assistant, system")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """Chat request model."""
    messages: List[ChatMessage] = Field(..., description="Chat messages")
    model: str = Field(default="llama2", description="AI model to use")
    stream: bool = Field(default=False, description="Stream response")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Model options")


class ChatResponse(BaseModel):
    """Chat response model."""
    model: str = Field(..., description="Model used")
    created_at: datetime = Field(..., description="Response timestamp")
    message: ChatMessage = Field(..., description="Response message")
    done: bool = Field(..., description="Response completion status")
    total_duration: Optional[int] = Field(default=None, description="Total duration in nanoseconds")
    load_duration: Optional[int] = Field(default=None, description="Load duration in nanoseconds")
    prompt_eval_count: Optional[int] = Field(default=None, description="Prompt evaluation count")
    prompt_eval_duration: Optional[int] = Field(default=None, description="Prompt evaluation duration")
    eval_count: Optional[int] = Field(default=None, description="Response evaluation count")
    eval_duration: Optional[int] = Field(default=None, description="Response evaluation duration")


class OllamaClient:
    """Ollama client for AI assistant."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.session: Optional[Any] = None # aiohttp.ClientSession
        self.settings = get_settings()
        
        # Default models to try
        self.default_models = ["llama2", "codellama", "mistral", "phi"]
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
    
    async def _ensure_session(self):
        """Ensure session is created."""
        pass
    
    async def check_connection(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            await self._ensure_session()
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False
    
    async def list_models(self) -> List[AIModel]:
        """List available models."""
        try:
            await self._ensure_session()
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status != 200:
                    raise Exception(f"Failed to list models: {response.status}")
                
                data = await response.json()
                models = []
                
                for model_data in data.get("models", []):
                    model = AIModel(
                        name=model_data["name"],
                        size=model_data["size"],
                        modified=datetime.fromisoformat(model_data["modified"].replace("Z", "+00:00")),
                        digest=model_data["digest"]
                    )
                    models.append(model)
                
                return models
                
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama."""
        try:
            await self._ensure_session()
            
            logger.info(f"Pulling model: {model_name}")
            
            async with self.session.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name}
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to pull model: {response.status}")
                
                # Stream the pull progress
                async for line in response.content:
                    if line:
                        try:
                            progress = json.loads(line.decode())
                            status = progress.get("status", "")
                            logger.info(f"Pull progress: {status}")
                        except json.JSONDecodeError:
                            continue
                
                logger.info(f"Model {model_name} pulled successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
    
    async def get_available_model(self) -> Optional[str]:
        """Get the first available model."""
        models = await self.list_models()
        
        if models:
            # Return the first available model
            return models[0].name
        
        # Try to pull a default model
        for model_name in self.default_models:
            logger.info(f"Trying to pull model: {model_name}")
            if await self.pull_model(model_name):
                return model_name
        
        return None
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Send chat request to Ollama."""
        try:
            await self._ensure_session()
            
            # Prepare request payload
            payload = {
                "model": request.model,
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content
                    }
                    for msg in request.messages
                ],
                "stream": request.stream
            }
            
            if request.options:
                payload["options"] = request.options
            
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                if response.status != 200:
                    raise Exception(f"Chat request failed: {response.status}")
                
                data = await response.json()
                
                # Convert response
                response_message = ChatMessage(
                    role=data["message"]["role"],
                    content=data["message"]["content"],
                    timestamp=datetime.now(UTC)
                )
                
                return ChatResponse(
                    model=data["model"],
                    created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
                    message=response_message,
                    done=data["done"],
                    total_duration=data.get("total_duration"),
                    load_duration=data.get("load_duration"),
                    prompt_eval_count=data.get("prompt_eval_count"),
                    prompt_eval_duration=data.get("prompt_eval_duration"),
                    eval_count=data.get("eval_count"),
                    eval_duration=data.get("eval_duration")
                )
                
        except Exception as e:
            logger.error(f"Chat request failed: {e}")
            raise
    
    async def chat_stream(self, request: ChatRequest):
        """Stream chat response from Ollama."""
        try:
            await self._ensure_session()
            
            # Prepare request payload
            payload = {
                "model": request.model,
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content
                    }
                    for msg in request.messages
                ],
                "stream": True
            }
            
            if request.options:
                payload["options"] = request.options
            
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                if response.status != 200:
                    raise Exception(f"Chat stream failed: {response.status}")
                
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line.decode())
                            yield data
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"Chat stream failed: {e}")
            raise


# Global client instance
_ollama_client: Optional[OllamaClient] = None


async def get_ollama_client() -> OllamaClient:
    """Get or create Ollama client."""
    global _ollama_client
    
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    
    return _ollama_client


class AIAssistant:
    """AI Assistant for cálculo de tração."""
    
    def __init__(self):
        self.client: Optional[OllamaClient] = None
        self.model: Optional[str] = None
        self.system_prompt = """Você é um assistente de IA especializado em cálculo de tração de redes elétricas.

Seu objetivo é ajudar engenheiros e técnicos a:
1. Calcular tração em postes e estruturas
2. Selecionar materiais adequados
3. Interpretar resultados de cálculos
4. Sugerir otimizações de projeto
5. Explicar conceitos técnicos

Responda de forma clara, concisa e técnica. Use exemplos práticos quando relevante.
Sempre considere as normas técnicas brasileiras e boas práticas de engenharia."""
    
    async def initialize(self) -> bool:
        """Initialize AI assistant."""
        try:
            self.client = await get_ollama_client()
            
            # Check connection
            if not await self.client.check_connection():
                logger.error("Ollama is not running. Please start Ollama first.")
                return False
            
            # Get available model
            self.model = await self.client.get_available_model()
            if not self.model:
                logger.error("No AI model available")
                return False
            
            logger.info(f"AI Assistant initialized with model: {self.model}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AI Assistant: {e}")
            return False
    
    async def chat(self, message: str, conversation_history: Optional[List[ChatMessage]] = None) -> str:
        """Chat with AI assistant."""
        if not self.client or not self.model:
            raise Exception("AI Assistant not initialized")
        
        try:
            # Prepare messages
            messages = []
            
            # Add system prompt
            messages.append(ChatMessage(
                role="system",
                content=self.system_prompt
            ))
            
            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history[-10:])  # Last 10 messages
            
            # Add current message
            messages.append(ChatMessage(
                role="user",
                content=message
            ))
            
            # Create request
            request = ChatRequest(
                messages=messages,
                model=self.model,
                stream=False,
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 1000
                }
            )
            
            # Send request
            response = await self.client.chat(request)
            
            return response.message.content
            
        except Exception as e:
            logger.error(f"AI chat failed: {e}")
            raise
    
    async def stream_chat(self, message: str, conversation_history: Optional[List[ChatMessage]] = None):
        """Stream chat response."""
        if not self.client or not self.model:
            raise Exception("AI Assistant not initialized")
        
        try:
            # Prepare messages
            messages = []
            
            # Add system prompt
            messages.append(ChatMessage(
                role="system",
                content=self.system_prompt
            ))
            
            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history[-10:])
            
            # Add current message
            messages.append(ChatMessage(
                role="user",
                content=message
            ))
            
            # Create request
            request = ChatRequest(
                messages=messages,
                model=self.model,
                stream=True,
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 1000
                }
            )
            
            # Stream response
            async for chunk in self.client.chat_stream(request):
                if chunk.get("message", {}).get("content"):
                    yield chunk["message"]["content"]
                    
        except Exception as e:
            logger.error(f"AI stream chat failed: {e}")
            raise
    
    async def analyze_calculation(self, calculation_data: Dict[str, Any]) -> str:
        """Analyze calculation results and provide insights."""
        try:
            # Prepare analysis prompt
            prompt = f"""Analise os seguintes dados de cálculo de tração:

{json.dumps(calculation_data, indent=2, ensure_ascii=False)}

Forneça uma análise técnica incluindo:
1. Validação dos resultados
2. Possíveis otimizações
3. Riscos identificados
4. Recomendações de melhoria
5. Conformidade com normas técnicas

Seja específico e técnico na sua análise."""
            
            return await self.chat(prompt)
            
        except Exception as e:
            logger.error(f"Failed to analyze calculation: {e}")
            raise
    
    async def suggest_optimization(self, project_data: Dict[str, Any]) -> str:
        """Suggest optimizations for a project."""
        try:
            # Prepare optimization prompt
            prompt = f"""Analise o seguinte projeto e sugira otimizações:

{json.dumps(project_data, indent=2, ensure_ascii=False)}

Sugira otimizações para:
1. Redução de custos
2. Melhoria de performance
3. Segurança estrutural
4. Eficiência energética
5. Sustentabilidade

Forneça sugestões práticas e implementáveis."""
            
            return await self.chat(prompt)
            
        except Exception as e:
            logger.error(f"Failed to suggest optimizations: {e}")
            raise


# Global AI assistant instance
_ai_assistant: Optional[AIAssistant] = None


async def get_ai_assistant() -> AIAssistant:
    """Get or create AI assistant."""
    global _ai_assistant
    
    if _ai_assistant is None:
        _ai_assistant = AIAssistant()
        await _ai_assistant.initialize()
    
    return _ai_assistant
