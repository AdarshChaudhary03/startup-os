from fastapi import APIRouter
from datetime import datetime
import psutil
import os
from config import db, gemini_client

health_router = APIRouter(prefix="/health", tags=["health"])


@health_router.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "AI Startup System Backend"
    }


@health_router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with system metrics and dependencies."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "AI Startup System Backend",
        "version": "1.0.0",
        "dependencies": {},
        "system": {}
    }
    
    # Check database connectivity
    try:
        # Simple ping to check MongoDB connection
        await db.command("ping")
        health_status["dependencies"]["mongodb"] = {
            "status": "healthy",
            "message": "Connected successfully"
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["dependencies"]["mongodb"] = {
            "status": "unhealthy",
            "message": f"Connection failed: {str(e)}"
        }
    
    # Check Gemini API availability
    if gemini_client:
        health_status["dependencies"]["gemini_api"] = {
            "status": "configured",
            "message": "API key configured"
        }
    else:
        health_status["status"] = "degraded"
        health_status["dependencies"]["gemini_api"] = {
            "status": "unconfigured",
            "message": "API key not configured"
        }
    
    # System metrics
    try:
        health_status["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "process_id": os.getpid(),
            "uptime_seconds": psutil.Process().create_time()
        }
    except Exception as e:
        health_status["system"] = {
            "error": f"Could not retrieve system metrics: {str(e)}"
        }
    
    return health_status


@health_router.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe endpoint."""
    try:
        # Check critical dependencies
        await db.command("ping")
        
        if not gemini_client:
            return {
                "status": "not_ready",
                "message": "Gemini API not configured"
            }, 503
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "message": f"Dependency check failed: {str(e)}"
        }, 503


@health_router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe endpoint."""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }