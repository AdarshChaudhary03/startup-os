"""AI Routes Module

API routes for managing AI providers and configurations.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from ..core.ai_startup import (
    get_ai_provider_info,
    switch_default_provider
)
from ..services.ai_service import ai_service
from ..core.config import AI_PROVIDER_MODELS

ai_router = APIRouter(prefix="/ai", tags=["AI Providers"])


class GenerateContentRequest(BaseModel):
    """Request model for content generation."""
    prompt: str
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1024


class GenerateContentResponse(BaseModel):
    """Response model for content generation."""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class ProviderSwitchRequest(BaseModel):
    """Request model for switching default provider."""
    provider_name: str


@ai_router.get("/providers")
async def get_providers():
    """Get information about all available AI providers."""
    try:
        provider_info = await get_ai_provider_info()
        return {
            "success": True,
            "data": provider_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get provider info: {e}")


@ai_router.get("/providers/health")
async def check_providers_health(provider: Optional[str] = Query(None)):
    """Check health status of AI providers."""
    try:
        health_status = await ai_service.health_check(provider)
        return {
            "success": True,
            "data": health_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {e}")


@ai_router.post("/providers/switch")
async def switch_provider(request: ProviderSwitchRequest):
    """Switch the default AI provider."""
    try:
        success = await switch_default_provider(request.provider_name)
        if success:
            return {
                "success": True,
                "message": f"Default provider switched to {request.provider_name}"
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to switch to provider: {request.provider_name}"
            )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Provider switch failed: {e}")


@ai_router.get("/models")
async def get_available_models(provider: Optional[str] = Query(None)):
    """Get available models for a specific provider or all providers."""
    try:
        if provider:
            if provider not in AI_PROVIDER_MODELS:
                raise HTTPException(status_code=404, detail=f"Provider {provider} not found")
            
            return {
                "success": True,
                "data": {
                    provider: AI_PROVIDER_MODELS[provider]
                }
            }
        else:
            return {
                "success": True,
                "data": AI_PROVIDER_MODELS
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get models: {e}")


@ai_router.post("/generate", response_model=GenerateContentResponse)
async def generate_content(request: GenerateContentRequest):
    """Generate content using the specified or default AI provider."""
    try:
        if not request.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")
        
        response = await ai_service.generate_content(
            prompt=request.prompt,
            provider_name=request.provider,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return GenerateContentResponse(
            content=response.content,
            model=response.model,
            provider=response.provider,
            usage=response.usage,
            metadata=response.metadata
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content generation failed: {e}")


@ai_router.get("/status")
async def get_ai_service_status():
    """Get overall AI service status."""
    try:
        is_initialized = ai_service.is_initialized()
        providers = ai_service.list_providers()
        default_provider = ai_service.get_default_provider_name()
        
        return {
            "success": True,
            "data": {
                "initialized": is_initialized,
                "providers_count": len(providers),
                "providers": list(providers.keys()),
                "default_provider": default_provider
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get service status: {e}")


@ai_router.get("/test")
async def test_ai_provider(
    provider: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    prompt: str = Query("Hello, how are you?")
):
    """Test an AI provider with a simple prompt."""
    try:
        response = await ai_service.generate_content(
            prompt=prompt,
            provider_name=provider,
            model=model,
            max_tokens=100
        )
        
        return {
            "success": True,
            "data": {
                "provider": response.provider,
                "model": response.model,
                "prompt": prompt,
                "response": response.content,
                "usage": response.usage
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Provider test failed: {e}")
