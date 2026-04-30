from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging
import uuid

from ceo_chat_interface import ceo_chat_interface, ChatSessionState
from ceo_requirements_analyzer import ceo_requirements_analyzer
from ceo_agent_planner import ceo_agent_planner
from models import CEORequirementsRequest
from logging_config import log_orchestration_event

# Create CEO chat router
ceo_chat_router = APIRouter(prefix="/api/ceo/chat")

# Initialize logger
logger = logging.getLogger(__name__)


@ceo_chat_router.post("/start")
async def start_chat_session(request_data: Dict[str, Any], request: Request):
    """Start a new CEO chat session for requirements gathering"""
    
    try:
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Extract the initial_message from the request data
        initial_message = request_data.get("initial_message")
        if not initial_message:
            raise HTTPException(status_code=422, detail="initial_message is required")
        
        log_orchestration_event(
            request_id=request_id,
            event_type="ceo_chat_start",
            message="Starting CEO interactive chat session",
            additional_data={
                "task": initial_message[:100] + "..." if len(initial_message) > 100 else initial_message,
                "user_context": request_data.get("user_context")
            }
        )
        
        # Start chat session
        session_info = ceo_chat_interface.start_chat_session(
            task=initial_message,
            user_context=request_data.get("user_context")
        )
        
        # Return the expected response structure for the frontend
        return {
            "conversation_id": session_info["session_id"],
            "state": "gathering_requirements",
            "message": session_info["greeting"],
            "requirements": {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@ceo_chat_router.post("/respond/{session_id}")
async def submit_response(session_id: str, response_data: Dict[str, Any], request: Request):
    """Submit a response to a CEO chat question"""
    
    try:
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        question_id = response_data.get("question_id")
        response = response_data.get("response")
        
        if not question_id or not response:
            raise HTTPException(status_code=400, detail="question_id and response are required")
        
        log_orchestration_event(
            request_id=request_id,
            event_type="ceo_chat_response",
            message=f"Processing response for question {question_id}",
            additional_data={
                "session_id": session_id,
                "question_id": question_id
            }
        )
        
        # Process response
        result = ceo_chat_interface.process_user_response(
            session_id=session_id,
            question_id=question_id,
            response=response
        )
        
        return {
            "status": "success",
            "action": result["action"],
            "message": result.get("message", ""),
            "next_question": result.get("question"),
            "questions_remaining": result.get("questions_remaining"),
            "requirements_summary": result.get("requirements_summary"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to process response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@ceo_chat_router.post("/confirm/{session_id}")
async def confirm_requirements(session_id: str, confirmation_data: Dict[str, Any], request: Request):
    """Confirm or adjust requirements"""
    
    try:
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        confirmed = confirmation_data.get("confirmed", False)
        adjustments = confirmation_data.get("adjustments")
        
        log_orchestration_event(
            request_id=request_id,
            event_type="ceo_chat_confirmation",
            message=f"Requirements {'confirmed' if confirmed else 'need adjustment'}",
            additional_data={
                "session_id": session_id,
                "confirmed": confirmed
            }
        )
        
        # Process confirmation
        result = ceo_chat_interface.confirm_requirements(
            session_id=session_id,
            confirmed=confirmed,
            adjustments=adjustments
        )
        
        response = {
            "status": "success",
            "action": result["action"],
            "message": result["message"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if result["action"] == "requirements_complete":
            # Generate comprehensive analysis and plan
            session_data = ceo_chat_interface.active_sessions.get(session_id, {})
            polished_requirements = result["polished_requirements"]
            
            # Perform comprehensive analysis
            analysis = await ceo_requirements_analyzer.analyze_requirements(
                task=session_data.get("original_task", ""),
                responses=session_data.get("responses", {}),
                context=session_data,
                request_id=request_id
            )
            
            # Create agent plan
            agent_plan = await ceo_agent_planner.create_agent_plan(
                requirements=polished_requirements.dict(),
                request_id=request_id
            )
            
            response.update({
                "polished_requirements": polished_requirements.dict(),
                "analysis": analysis,
                "agent_plan": agent_plan,
                "next_step": "proceed_to_execution"
            })
        else:
            response.update({
                "requirements_summary": result.get("requirements_summary"),
                "next_step": result.get("next_step")
            })
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to confirm requirements: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@ceo_chat_router.get("/status/{session_id}")
async def get_chat_status(session_id: str):
    """Get the current status of a chat session"""
    
    try:
        status = ceo_chat_interface.get_session_status(session_id)
        
        if status["status"] == "not_found":
            raise HTTPException(status_code=404, detail=status["message"])
        
        return {
            "status": "success",
            "session_info": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@ceo_chat_router.post("/analyze/{session_id}")
async def analyze_requirements(session_id: str, request: Request):
    """Perform comprehensive requirements analysis for a session"""
    
    try:
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Get session data
        if session_id not in ceo_chat_interface.active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = ceo_chat_interface.active_sessions[session_id]
        
        # Check if session is ready for analysis
        if session_data["state"] not in [ChatSessionState.CONFIRMING_REQUIREMENTS, ChatSessionState.COMPLETE]:
            raise HTTPException(
                status_code=400, 
                detail="Session not ready for analysis. Complete requirements gathering first."
            )
        
        log_orchestration_event(
            request_id=request_id,
            event_type="ceo_requirements_analysis",
            message="Performing comprehensive requirements analysis",
            additional_data={"session_id": session_id}
        )
        
        # Perform analysis
        analysis = await ceo_requirements_analyzer.analyze_requirements(
            task=session_data.get("original_task", ""),
            responses=session_data.get("responses", {}),
            context=session_data,
            request_id=request_id
        )
        
        # Generate documentation
        documentation = ceo_requirements_analyzer.generate_documentation(
            analysis, format="markdown"
        )
        
        return {
            "status": "success",
            "session_id": session_id,
            "analysis": analysis,
            "documentation": documentation,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze requirements: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@ceo_chat_router.post("/plan/{session_id}")
async def create_execution_plan(session_id: str, request: Request):
    """Create agent execution plan for a session"""
    
    try:
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Get session data
        if session_id not in ceo_chat_interface.active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = ceo_chat_interface.active_sessions[session_id]
        
        # Check if requirements are complete
        if "polished_requirements" not in session_data:
            raise HTTPException(
                status_code=400,
                detail="Requirements not finalized. Complete requirements confirmation first."
            )
        
        log_orchestration_event(
            request_id=request_id,
            event_type="ceo_agent_planning",
            message="Creating agent execution plan",
            additional_data={"session_id": session_id}
        )
        
        # Create agent plan
        polished_requirements = session_data["polished_requirements"]
        agent_plan = await ceo_agent_planner.create_agent_plan(
            requirements=polished_requirements.dict() if hasattr(polished_requirements, 'dict') else polished_requirements,
            request_id=request_id
        )
        
        # Validate plan
        if agent_plan.get("success"):
            is_valid, issues = ceo_agent_planner.validate_plan(agent_plan["plan"])
            
            if not is_valid:
                return {
                    "status": "warning",
                    "message": "Plan created with validation issues",
                    "plan": agent_plan,
                    "validation_issues": issues,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
        
        return {
            "status": "success",
            "session_id": session_id,
            "agent_plan": agent_plan,
            "ready_for_execution": agent_plan.get("success", False),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create execution plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@ceo_chat_router.get("/sessions")
async def list_active_sessions():
    """List all active chat sessions"""
    
    try:
        sessions = []
        
        for session_id, session_data in ceo_chat_interface.active_sessions.items():
            sessions.append({
                "session_id": session_id,
                "state": session_data["state"].value,
                "created_at": session_data["created_at"],
                "updated_at": session_data["updated_at"],
                "questions_asked": len(session_data.get("questions_asked", [])),
                "is_complete": session_data["state"] == ChatSessionState.COMPLETE
            })
        
        return {
            "status": "success",
            "total_sessions": len(sessions),
            "sessions": sessions,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Export router
__all__ = ["ceo_chat_router"]
