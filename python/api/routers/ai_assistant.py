"""Router for AI Assistant endpoints."""
from __future__ import annotations

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ai.ollama_client import get_ai_assistant, ChatMessage
from core.config import get_settings

router = APIRouter(prefix="/ai", tags=["AI Assistant"])
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID")
    stream: bool = Field(default=False, description="Stream response")


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str = Field(..., description="AI response")
    conversation_id: str = Field(..., description="Conversation ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model: str = Field(..., description="AI model used")


class AnalysisRequest(BaseModel):
    """Analysis request model."""
    calculation_data: Dict[str, Any] = Field(..., description="Calculation data to analyze")
    analysis_type: str = Field(default="general", description="Type of analysis")


class OptimizationRequest(BaseModel):
    """Optimization request model."""
    project_data: Dict[str, Any] = Field(..., description="Project data to optimize")
    optimization_goals: List[str] = Field(default=["cost", "performance"], description="Optimization goals")


# In-memory conversation storage (in production, use Redis or database)
conversations: Dict[str, List[ChatMessage]] = {}


@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest) -> ChatResponse:
    """Chat with AI assistant."""
    try:
        # Get AI assistant
        ai_assistant = await get_ai_assistant()
        
        # Get or create conversation ID
        conversation_id = request.conversation_id or f"conv_{datetime.utcnow().timestamp()}"
        
        # Get conversation history
        history = conversations.get(conversation_id, [])
        
        # Chat with AI
        response = await ai_assistant.chat(request.message, history)
        
        # Update conversation history
        if conversation_id not in conversations:
            conversations[conversation_id] = []
        
        conversations[conversation_id].extend([
            ChatMessage(role="user", content=request.message),
            ChatMessage(role="assistant", content=response)
        ])
        
        # Limit conversation history to last 20 messages
        if len(conversations[conversation_id]) > 20:
            conversations[conversation_id] = conversations[conversation_id][-20:]
        
        return ChatResponse(
            response=response,
            conversation_id=conversation_id,
            model=ai_assistant.model or "unknown"
        )
        
    except Exception as e:
        logger.error(f"AI chat failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process AI chat request"
        )


@router.post("/chat/stream")
async def stream_chat_with_ai(request: ChatRequest):
    """Stream chat with AI assistant."""
    try:
        # Get AI assistant
        ai_assistant = await get_ai_assistant()
        
        # Get or create conversation ID
        conversation_id = request.conversation_id or f"conv_{datetime.utcnow().timestamp()}"
        
        # Get conversation history
        history = conversations.get(conversation_id, [])
        
        async def generate():
            try:
                full_response = ""
                
                # Stream response from AI
                async for chunk in ai_assistant.stream_chat(request.message, history):
                    full_response += chunk
                    yield f"data: {json.dumps({'chunk': chunk, 'conversation_id': conversation_id})}\n\n"
                
                # Update conversation history
                if conversation_id not in conversations:
                    conversations[conversation_id] = []
                
                conversations[conversation_id].extend([
                    ChatMessage(role="user", content=request.message),
                    ChatMessage(role="assistant", content=full_response)
                ])
                
                # Limit conversation history
                if len(conversations[conversation_id]) > 20:
                    conversations[conversation_id] = conversations[conversation_id][-20:]
                
                # Send completion signal
                yield f"data: {json.dumps({'done': True, 'conversation_id': conversation_id})}\n\n"
                
            except Exception as e:
                logger.error(f"Stream chat failed: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
        
    except Exception as e:
        logger.error(f"AI stream chat failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process AI stream chat request"
        )


@router.post("/analyze/calculation")
async def analyze_calculation(request: AnalysisRequest) -> Dict[str, Any]:
    """Analyze calculation results with AI."""
    try:
        # Get AI assistant
        ai_assistant = await get_ai_assistant()
        
        # Analyze calculation
        analysis = await ai_assistant.analyze_calculation(request.calculation_data)
        
        return {
            "status": "success",
            "analysis": analysis,
            "analysis_type": request.analysis_type,
            "timestamp": datetime.utcnow().isoformat(),
            "model": ai_assistant.model or "unknown"
        }
        
    except Exception as e:
        logger.error(f"Calculation analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze calculation"
        )


@router.post("/optimize/project")
async def optimize_project(request: OptimizationRequest) -> Dict[str, Any]:
    """Optimize project with AI suggestions."""
    try:
        # Get AI assistant
        ai_assistant = await get_ai_assistant()
        
        # Prepare optimization prompt with goals
        goals_text = ", ".join(request.optimization_goals)
        project_data_with_goals = {
            **request.project_data,
            "optimization_goals": request.optimization_goals
        }
        
        # Get optimization suggestions
        suggestions = await ai_assistant.suggest_optimization(project_data_with_goals)
        
        return {
            "status": "success",
            "suggestions": suggestions,
            "optimization_goals": request.optimization_goals,
            "timestamp": datetime.utcnow().isoformat(),
            "model": ai_assistant.model or "unknown"
        }
        
    except Exception as e:
        logger.error(f"Project optimization failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to optimize project"
        )


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str) -> Dict[str, Any]:
    """Get conversation history."""
    try:
        history = conversations.get(conversation_id, [])
        
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                }
                for msg in history
            ],
            "message_count": len(history)
        }
        
    except Exception as e:
        logger.error(f"Failed to get conversation: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve conversation"
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str) -> Dict[str, Any]:
    """Delete conversation."""
    try:
        if conversation_id in conversations:
            del conversations[conversation_id]
        
        return {
            "status": "success",
            "message": f"Conversation {conversation_id} deleted",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete conversation"
        )


@router.get("/conversations")
async def list_conversations() -> Dict[str, Any]:
    """List all conversations."""
    try:
        conversation_list = []
        
        for conv_id, messages in conversations.items():
            conversation_list.append({
                "conversation_id": conv_id,
                "message_count": len(messages),
                "last_message": messages[-1].timestamp.isoformat() if messages else None,
                "preview": messages[-1].content[:100] + "..." if messages and len(messages[-1].content) > 100 else (messages[-1].content if messages else "")
            })
        
        # Sort by last message time
        conversation_list.sort(key=lambda x: x["last_message"] or "", reverse=True)
        
        return {
            "status": "success",
            "conversations": conversation_list,
            "total_count": len(conversation_list)
        }
        
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list conversations"
        )


@router.get("/status")
async def get_ai_status() -> Dict[str, Any]:
    """Get AI assistant status."""
    try:
        ai_assistant = await get_ai_assistant()
        
        # Get available models
        models = []
        if ai_assistant.client:
            model_list = await ai_assistant.client.list_models()
            models = [
                {
                    "name": model.name,
                    "size": model.size,
                    "modified": model.modified.isoformat(),
                    "digest": model.digest[:16] + "..."  # Short digest
                }
                for model in model_list
            ]
        
        return {
            "status": "success",
            "ai_initialized": ai_assistant.client is not None,
            "current_model": ai_assistant.model,
            "available_models": models,
            "ollama_connected": ai_assistant.client is not None and await ai_assistant.client.check_connection(),
            "active_conversations": len(conversations),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get AI status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "ai_initialized": False,
            "timestamp": datetime.utcnow().isoformat()
        }


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    
    try:
        # Get AI assistant
        ai_assistant = await get_ai_assistant()
        
        conversation_id = None
        history = []
        
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            message_type = data.get("type", "chat")
            
            if message_type == "chat":
                user_message = data.get("message", "")
                conversation_id = data.get("conversation_id")
                
                if not conversation_id:
                    conversation_id = f"ws_conv_{datetime.utcnow().timestamp()}"
                
                # Get conversation history
                history = conversations.get(conversation_id, [])
                
                # Stream response
                await websocket.send_json({
                    "type": "start",
                    "conversation_id": conversation_id
                })
                
                full_response = ""
                
                async for chunk in ai_assistant.stream_chat(user_message, history):
                    full_response += chunk
                    await websocket.send_json({
                        "type": "chunk",
                        "chunk": chunk,
                        "conversation_id": conversation_id
                    })
                
                # Update conversation history
                if conversation_id not in conversations:
                    conversations[conversation_id] = []
                
                conversations[conversation_id].extend([
                    ChatMessage(role="user", content=user_message),
                    ChatMessage(role="assistant", content=full_response)
                ])
                
                # Limit history
                if len(conversations[conversation_id]) > 20:
                    conversations[conversation_id] = conversations[conversation_id][-20:]
                
                await websocket.send_json({
                    "type": "end",
                    "conversation_id": conversation_id,
                    "full_response": full_response
                })
                
            elif message_type == "get_history":
                if conversation_id:
                    history = conversations.get(conversation_id, [])
                    await websocket.send_json({
                        "type": "history",
                        "conversation_id": conversation_id,
                        "messages": [
                            {
                                "role": msg.role,
                                "content": msg.content,
                                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                            }
                            for msg in history
                        ]
                    })
                
            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for conversation {conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "error": str(e)
            })
        except:
            pass
