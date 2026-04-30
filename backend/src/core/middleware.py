import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from .logging_config import log_api_request, log_api_response, log_error
import logging


class APILoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests and responses with timing and metadata."""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ['/health', '/metrics', '/favicon.ico']
        self.logger = logging.getLogger(__name__)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Extract request metadata
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get('user-agent', 'Unknown')
        method = request.method
        endpoint = request.url.path
        query_params = str(request.query_params) if request.query_params else None
        
        # Add request ID to request state for use in route handlers
        request.state.request_id = request_id
        
        # Log incoming request
        additional_request_data = {}
        if query_params:
            additional_request_data['query_params'] = query_params
        
        log_api_request(
            request_id=request_id,
            method=method,
            endpoint=endpoint,
            ip_address=client_ip,
            user_agent=user_agent,
            additional_data=additional_request_data
        )
        
        # Record start time
        start_time = time.time()
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful response
            additional_response_data = {}
            if hasattr(request.state, 'orchestration_mode'):
                additional_response_data['orchestration_mode'] = request.state.orchestration_mode
            if hasattr(request.state, 'agent_count'):
                additional_response_data['agent_count'] = request.state.agent_count
            
            log_api_response(
                request_id=request_id,
                status_code=response.status_code,
                duration_ms=duration_ms,
                additional_data=additional_response_data
            )
            
            # Add request ID to response headers for tracing
            response.headers['X-Request-ID'] = request_id
            
            return response
            
        except Exception as error:
            # Calculate duration for error case
            duration_ms = (time.time() - start_time) * 1000
            
            # Log the error
            log_error(
                request_id=request_id,
                error=error,
                context=f"Request processing failed for {method} {endpoint}",
                additional_data={
                    'duration_ms': duration_ms,
                    'ip_address': client_ip,
                    'user_agent': user_agent
                }
            )
            
            # Log error response
            status_code = 500
            if hasattr(error, 'status_code'):
                status_code = error.status_code
            
            log_api_response(
                request_id=request_id,
                status_code=status_code,
                duration_ms=duration_ms,
                additional_data={'error': str(error)}
            )
            
            # Return structured error response
            return JSONResponse(
                status_code=status_code,
                content={
                    'error': 'Internal server error',
                    'request_id': request_id,
                    'message': str(error) if not isinstance(error, Exception) else 'An unexpected error occurred'
                },
                headers={'X-Request-ID': request_id}
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request headers."""
        # Check for forwarded headers first (for proxy/load balancer scenarios)
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            # Take the first IP if multiple are present
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if request.client:
            return request.client.host
        
        return 'Unknown'


class OrchestrationLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware specifically for tracking orchestration patterns and debugging multi-agent issues."""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger('orchestration')
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only apply to orchestration endpoints
        if not request.url.path.startswith('/api/orchestrate'):
            return await call_next(request)
        
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        try:
            # Log orchestration start
            self.logger.info(
                f"Orchestration request started",
                extra={
                    'request_id': request_id,
                    'event_type': 'orchestration_start',
                    'endpoint': request.url.path
                }
            )
            
            response = await call_next(request)
            
            # Log orchestration completion
            self.logger.info(
                f"Orchestration request completed",
                extra={
                    'request_id': request_id,
                    'event_type': 'orchestration_complete',
                    'status_code': response.status_code
                }
            )
            
            return response
            
        except Exception as error:
            # Log orchestration failure
            self.logger.error(
                f"Orchestration request failed: {str(error)}",
                extra={
                    'request_id': request_id,
                    'event_type': 'orchestration_error',
                    'error_details': str(error)
                },
                exc_info=True
            )
            raise