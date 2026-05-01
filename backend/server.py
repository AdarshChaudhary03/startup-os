from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

# Import configuration
from src.core.config import CORS_ORIGINS, APP_TITLE, LOG_LEVEL, LOG_FORMAT

# Import logging configuration and middleware
from src.core.logging_config import setup_logging
from src.core.middleware import APILoggingMiddleware, OrchestrationLoggingMiddleware

# Import routes
from src.core.health import health_router
from src.routes.agent_routes import agent_router
from src.routes.orchestration_routes import orchestration_router
from src.routes.ceo_orchestration_routes import ceo_router
from src.agents.ceo.ceo_requirements_gathering import ceo_requirements_router
from src.routes.ceo_chat_routes import ceo_chat_router
from src.routes.ceo_chat_message_routes import ceo_message_router
from src.routes.ceo_simplified_routes import ceo_simplified_router

# Import exception handlers
from src.core.exceptions import (
    BaseAPIException,
    api_exception_handler,
    general_exception_handler,
    http_exception_handler
)

# Import AI startup functions
from src.core.ai_startup import initialize_ai_providers, cleanup_ai_providers

# Initialize logging before creating the app
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger = logging.getLogger(__name__)
    logger.info("Starting AI Startup System...")
    
    try:
        # Initialize AI providers
        await initialize_ai_providers()
        logger.info("AI providers initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AI providers: {e}")
        # Continue startup even if AI providers fail to initialize
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Startup System...")
    try:
        await cleanup_ai_providers()
        logger.info("AI providers cleanup completed")
    except Exception as e:
        logger.error(f"Error during AI providers cleanup: {e}")


app = FastAPI(title=APP_TITLE, lifespan=lifespan)

# Add logging middleware
app.add_middleware(APILoggingMiddleware, exclude_paths=['/health', '/metrics', '/favicon.ico'])
app.add_middleware(OrchestrationLoggingMiddleware)

# Import the main API router that includes the teams endpoint
from src.routes.routes import api_router

# Include API routes
app.include_router(health_router)
app.include_router(api_router)  # This includes the /api/teams endpoint
app.include_router(orchestration_router)  # Add orchestration routes for /api/orchestrate endpoint
app.include_router(agent_router)
app.include_router(ceo_router)
app.include_router(ceo_requirements_router)
app.include_router(ceo_chat_router)
app.include_router(ceo_message_router)
app.include_router(ceo_simplified_router)

# Add exception handlers
app.add_exception_handler(BaseAPIException, api_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure basic logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
