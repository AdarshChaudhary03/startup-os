from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Union
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseAPIException(Exception):
    """Base exception class for API errors."""
    def __init__(self, message: str, status_code: int = 500, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        super().__init__(self.message)


class AgentNotFoundException(BaseAPIException):
    """Raised when a requested agent is not found."""
    def __init__(self, agent_id: str):
        super().__init__(
            message=f"Agent '{agent_id}' not found",
            status_code=404,
            error_code="AGENT_NOT_FOUND"
        )


class TaskValidationException(BaseAPIException):
    """Raised when task validation fails."""
    def __init__(self, message: str = "Task validation failed"):
        super().__init__(
            message=message,
            status_code=400,
            error_code="TASK_VALIDATION_ERROR"
        )


class OrchestrationException(BaseAPIException):
    """Raised when orchestration fails."""
    def __init__(self, message: str = "Orchestration failed"):
        super().__init__(
            message=message,
            status_code=500,
            error_code="ORCHESTRATION_ERROR"
        )


class LLMServiceException(BaseAPIException):
    """Raised when LLM service is unavailable or fails."""
    def __init__(self, message: str = "LLM service unavailable"):
        super().__init__(
            message=message,
            status_code=503,
            error_code="LLM_SERVICE_ERROR"
        )


class DatabaseException(BaseAPIException):
    """Raised when database operations fail."""
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(
            message=message,
            status_code=500,
            error_code="DATABASE_ERROR"
        )


async def api_exception_handler(request: Request, exc: BaseAPIException):
    """Global exception handler for custom API exceptions."""
    logger.error(
        f"API Exception: {exc.error_code} - {exc.message} "
        f"(Status: {exc.status_code}, Path: {request.url.path})"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path)
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    logger.exception(
        f"Unhandled exception: {type(exc).__name__} - {str(exc)} "
        f"(Path: {request.url.path})"
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path)
            }
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Global exception handler for FastAPI HTTP exceptions."""
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail} "
        f"(Path: {request.url.path})"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path)
            }
        }
    )