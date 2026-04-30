import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, Any


class APIRequestFormatter(logging.Formatter):
    """Custom formatter for API request logging with structured JSON output."""
    
    def format(self, record):
        # Create base log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage()
        }
        
        # Add API-specific fields if available
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'duration_ms'):
            log_entry['duration_ms'] = record.duration_ms
        if hasattr(record, 'user_agent'):
            log_entry['user_agent'] = record.user_agent
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
        if hasattr(record, 'agent_id'):
            log_entry['agent_id'] = record.agent_id
        if hasattr(record, 'orchestration_mode'):
            log_entry['orchestration_mode'] = record.orchestration_mode
        if hasattr(record, 'error_details'):
            log_entry['error_details'] = record.error_details
            
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging():
    """Configure logging for the application with file rotation and structured output."""
    
    # Create logs directory under backend root
    backend_root = Path(__file__).parent  # Current file is now in backend root
    log_dir = backend_root / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Console handler for development
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    
    # File handler for general application logs with rotation
    app_log_file = log_dir / 'app.log'
    app_file_handler = logging.handlers.RotatingFileHandler(
        app_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    app_file_handler.setFormatter(console_formatter)
    app_file_handler.setLevel(logging.INFO)
    
    # API request handler for structured API logging
    api_log_file = log_dir / 'api_requests.log'
    api_file_handler = logging.handlers.RotatingFileHandler(
        api_log_file,
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=10,
        encoding='utf-8'
    )
    api_file_handler.setFormatter(APIRequestFormatter())
    api_file_handler.setLevel(logging.INFO)
    
    # Error handler for error-only logs
    error_log_file = log_dir / 'errors.log'
    error_file_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_file_handler.setFormatter(console_formatter)
    error_file_handler.setLevel(logging.ERROR)
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(app_file_handler)
    root_logger.addHandler(error_file_handler)
    
    # Create API logger for request/response logging
    api_logger = logging.getLogger('api_requests')
    api_logger.setLevel(logging.INFO)
    api_logger.addHandler(api_file_handler)
    api_logger.propagate = False  # Don't propagate to root logger
    
    # Create orchestration logger for agent execution tracking
    orchestration_log_file = log_dir / 'orchestration.log'
    orchestration_file_handler = logging.handlers.RotatingFileHandler(
        orchestration_log_file,
        maxBytes=25 * 1024 * 1024,  # 25MB
        backupCount=7,
        encoding='utf-8'
    )
    orchestration_file_handler.setFormatter(APIRequestFormatter())
    
    orchestration_logger = logging.getLogger('orchestration')
    orchestration_logger.setLevel(logging.INFO)
    orchestration_logger.addHandler(orchestration_file_handler)
    orchestration_logger.propagate = False
    
    logging.info("Logging system initialized successfully")
    logging.info(f"Log files will be created in: {log_dir.absolute()}")


def get_api_logger():
    """Get the API request logger instance."""
    return logging.getLogger('api_requests')


def get_orchestration_logger():
    """Get the orchestration logger instance."""
    return logging.getLogger('orchestration')


def log_api_request(request_id: str, method: str, endpoint: str, 
                   ip_address: str = None, user_agent: str = None,
                   additional_data: Dict[str, Any] = None):
    """Log an incoming API request."""
    logger = get_api_logger()
    
    extra_data = {
        'request_id': request_id,
        'method': method,
        'endpoint': endpoint,
    }
    
    if ip_address:
        extra_data['ip_address'] = ip_address
    if user_agent:
        extra_data['user_agent'] = user_agent
    if additional_data:
        extra_data.update(additional_data)
    
    logger.info(f"API Request: {method} {endpoint}", extra=extra_data)


def log_api_response(request_id: str, status_code: int, duration_ms: float,
                    additional_data: Dict[str, Any] = None):
    """Log an API response."""
    logger = get_api_logger()
    
    extra_data = {
        'request_id': request_id,
        'status_code': status_code,
        'duration_ms': round(duration_ms, 2)
    }
    
    if additional_data:
        extra_data.update(additional_data)
    
    logger.info(f"API Response: {status_code} ({duration_ms:.2f}ms)", extra=extra_data)


def log_orchestration_event(request_id: str, event_type: str, agent_id: str = None,
                           orchestration_mode: str = None, message: str = None,
                           additional_data: Dict[str, Any] = None):
    """Log orchestration events for debugging multi-agent issues."""
    logger = get_orchestration_logger()
    
    extra_data = {
        'request_id': request_id,
        'event_type': event_type,
    }
    
    if agent_id:
        extra_data['agent_id'] = agent_id
    if orchestration_mode:
        extra_data['orchestration_mode'] = orchestration_mode
    if additional_data:
        extra_data.update(additional_data)
    
    log_message = message or f"Orchestration event: {event_type}"
    logger.info(log_message, extra=extra_data)


def log_error(request_id: str, error: Exception, context: str = None,
             additional_data: Dict[str, Any] = None):
    """Log errors with structured context."""
    logger = logging.getLogger(__name__)
    
    extra_data = {
        'request_id': request_id,
        'error_type': type(error).__name__,
        'error_details': str(error)
    }
    
    if context:
        extra_data['context'] = context
    if additional_data:
        extra_data.update(additional_data)
    
    logger.error(f"Error occurred: {str(error)}", extra=extra_data, exc_info=True)