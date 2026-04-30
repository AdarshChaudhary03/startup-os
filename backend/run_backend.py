#!/usr/bin/env python3
"""
Backend Server Runner with Enhanced Logging

This script starts the FastAPI server with proper logging configuration
and provides utilities for monitoring and debugging.
"""

import uvicorn
import os
import sys
from pathlib import Path
from src.core.logging_config import setup_logging
import logging
from dotenv import load_dotenv


def check_environment():
    """Check if all required environment variables are set."""
    required_vars = ['MONGO_URL', 'DB_NAME', 'GEMINI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("[ERROR] Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file or environment.")
        return False
    
    print("[SUCCESS] All required environment variables are set.")
    return True


def setup_log_directories():
    """Ensure log directories exist."""
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    print(f"[INFO] Log directory: {log_dir.absolute()}")
    return log_dir


def main():
    """Main function to start the server."""
    print("Starting AI Startup System Backend...")
    print("=" * 50)
    
    # Load environment variables from .env file
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[SUCCESS] Loaded environment variables from: {env_path}")
    else:
        print(f"[WARNING] No .env file found at: {env_path}")
    
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Setup log directories
    log_dir = setup_log_directories()
    
    # Configuration
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    
    print(f"[INFO] Server will start on: http://{host}:{port}")
    print(f"[INFO] Debug mode: {debug}")
    print(f"[INFO] Logs will be written to: {log_dir}")
    print("")
    print("[INFO] Available log files:")
    print("   - app.log: General application logs")
    print("   - api_requests.log: API request/response logs (JSON format)")
    print("   - orchestration.log: Agent orchestration tracking (JSON format)")
    print("   - errors.log: Error-only logs")
    print("")
    print("[INFO] Debugging tools:")
    print("   - python orchestration_analyzer.py: Analyze orchestration patterns")
    print("   - tail -f logs/orchestration.log: Monitor live orchestration")
    print("   - tail -f logs/api_requests.log: Monitor live API requests")
    print("")
    print("=" * 50)
    
    logger.info(f"Starting server on {host}:{port} with debug={debug}")
    
    try:
        # Start the server
        uvicorn.run(
            "server:app",
            host=host,
            port=port,
            reload=debug,
            log_level="info" if not debug else "debug",
            access_log=False,  # We handle our own access logging
        )
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
        print("\n[INFO] Server stopped gracefully.")
    except Exception as e:
        logger.error(f"Server startup failed: {e}", exc_info=True)
        print(f"[ERROR] Server failed to start: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
