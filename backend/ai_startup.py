"""AI Startup Module

Initialization and configuration for AI providers in the startup system.
"""

import logging
from typing import Optional

from ai_service import ai_service
from config import (
    GEMINI_API_KEY,
    GROQ_API_KEY, 
    OPENAI_ROUTER_API_KEY,
    DEFAULT_AI_PROVIDER,
    AI_PROVIDER_MODELS
)

logger = logging.getLogger(__name__)


async def initialize_ai_providers() -> None:
    """Initialize AI providers based on available API keys.
    
    This function sets up all available AI providers and configures
    the default provider based on the configuration.
    """
    providers_added = []
    
    try:
        # Initialize Gemini provider if API key is available
        if GEMINI_API_KEY:
            await ai_service.add_provider(
                name="gemini",
                provider_type="gemini",
                api_key=GEMINI_API_KEY,
                is_default=(DEFAULT_AI_PROVIDER == "gemini")
            )
            providers_added.append("gemini")
            logger.info("Gemini provider initialized successfully")
        
        # Initialize Groq provider if API key is available
        if GROQ_API_KEY:
            await ai_service.add_provider(
                name="groq",
                provider_type="groq", 
                api_key=GROQ_API_KEY,
                is_default=(DEFAULT_AI_PROVIDER == "groq")
            )
            providers_added.append("groq")
            logger.info("Groq provider initialized successfully")
        
        # Initialize OpenAI Router provider if API key is available
        if OPENAI_ROUTER_API_KEY:
            await ai_service.add_provider(
                name="openai_router",
                provider_type="openai_router",
                api_key=OPENAI_ROUTER_API_KEY,
                is_default=(DEFAULT_AI_PROVIDER == "openai_router")
            )
            providers_added.append("openai_router")
            logger.info("OpenAI Router provider initialized successfully")
        
        if not providers_added:
            logger.warning(
                "No AI providers could be initialized. "
                "Please check your API key configuration."
            )
        else:
            default_provider = ai_service.get_default_provider_name()
            logger.info(
                f"AI providers initialized: {providers_added}. "
                f"Default provider: {default_provider}"
            )
    
    except Exception as e:
        logger.error(f"Failed to initialize AI providers: {e}")
        raise


async def get_ai_provider_info() -> dict:
    """Get information about available AI providers.
    
    Returns:
        Dict containing provider information including models and status
    """
    providers = ai_service.list_providers()
    default_provider = ai_service.get_default_provider_name()
    health_status = await ai_service.health_check()
    
    provider_info = {}
    
    for name, provider_type in providers.items():
        provider_config = AI_PROVIDER_MODELS.get(provider_type, {})
        
        provider_info[name] = {
            "type": provider_type,
            "is_default": name == default_provider,
            "is_healthy": health_status.get(name, False),
            "default_model": provider_config.get("default"),
            "available_models": provider_config.get("models", [])
        }
    
    return {
        "providers": provider_info,
        "default_provider": default_provider,
        "total_providers": len(providers)
    }


async def switch_default_provider(provider_name: str) -> bool:
    """Switch the default AI provider.
    
    Args:
        provider_name: Name of the provider to set as default
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        ai_service.set_default_provider(provider_name)
        logger.info(f"Switched default AI provider to: {provider_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to switch default provider to {provider_name}: {e}")
        return False


async def cleanup_ai_providers() -> None:
    """Cleanup AI providers on application shutdown."""
    try:
        await ai_service.cleanup()
        logger.info("AI providers cleanup completed")
    except Exception as e:
        logger.error(f"Error during AI providers cleanup: {e}")


# Backward compatibility function for existing code
async def ceo_plan_with_llm_new(
    task: str, 
    session_id: str,
    provider_name: Optional[str] = None,
    model: Optional[str] = None
) -> Optional[dict]:
    """New implementation of CEO planning with pluggable AI providers.
    
    This replaces the old ceo_plan_with_llm function with support for
    multiple AI providers while maintaining the same interface.
    
    Args:
        task: The task to plan for
        session_id: Session ID for logging
        provider_name: Specific provider to use (optional)
        model: Specific model to use (optional)
        
    Returns:
        Planning result dict or None if failed
    """
    from utils import (
        CEO_SYSTEM_PROMPT, 
        build_agent_catalog, 
        _extract_json, 
        _validate_plan
    )
    from logging_config import log_orchestration_event
    
    if not ai_service.is_initialized():
        log_orchestration_event(
            request_id=session_id,
            event_type="llm_unavailable",
            message="No AI providers available for planning"
        )
        return None
    
    try:
        catalog = build_agent_catalog()
        system_message = CEO_SYSTEM_PROMPT.format(catalog=catalog)
        prompt = f"{system_message}\n\nUSER DIRECTIVE: {task}\n\nReturn the JSON plan now."
        
        # Generate response using the new AI service
        response = await ai_service.generate_content(
            prompt=prompt,
            provider_name=provider_name,
            model=model
        )
        
        raw = response.content
        
        plan = _extract_json(raw)
        if not plan:
            log_orchestration_event(
                request_id=session_id,
                event_type="llm_json_parse_failed",
                message="Failed to parse JSON from LLM response",
                additional_data={"raw_response_preview": str(raw)[:200]}
            )
            logger.warning("CEO LLM: failed to parse JSON. Raw: %s", str(raw)[:300])
            return None
        
        cleaned = _validate_plan(plan)
        if not cleaned:
            log_orchestration_event(
                request_id=session_id,
                event_type="llm_plan_validation_failed",
                message="LLM plan failed validation",
                additional_data={"raw_plan": plan}
            )
            logger.warning("CEO LLM: invalid plan after validation: %s", plan)
            return None
        
        return cleaned
        
    except Exception as e:
        log_orchestration_event(
            request_id=session_id,
            event_type="llm_call_error",
            message=f"LLM call failed: {str(e)}",
            additional_data={"error_type": type(e).__name__}
        )
        logger.exception("CEO LLM call failed: %s", e)
        return None