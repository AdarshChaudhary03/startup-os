from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
from datetime import datetime, timezone
import logging
import uuid

from src.agents.ceo.ceo_chat_interface import ceo_chat_interface, ChatSessionState
from src.agents.ceo.ceo_conversation_flow import ceo_conversation_flow
from src.core.logging_config import log_orchestration_event

# Create message router
ceo_message_router = APIRouter()

# Initialize logger
logger = logging.getLogger(__name__)


@ceo_message_router.post("/api/ceo/chat/message")
async def send_chat_message(request_data: Dict[str, Any], request: Request):
    """Send a message in an existing CEO chat session"""
    
    try:
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Extract required fields
        conversation_id = request_data.get("conversation_id")
        message = request_data.get("message")
        
        if not conversation_id or not message:
            raise HTTPException(status_code=422, detail="conversation_id and message are required")
        
        # Check if session exists
        if conversation_id not in ceo_chat_interface.active_sessions:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        session_data = ceo_chat_interface.active_sessions[conversation_id]
        
        log_orchestration_event(
            request_id=request_id,
            event_type="ceo_chat_message",
            message="Processing user message in CEO chat",
            additional_data={
                "conversation_id": conversation_id,
                "message_preview": message[:50] + "..." if len(message) > 50 else message
            }
        )
        
        # Process the message through conversation flow
        flow_result = await ceo_conversation_flow.process_user_message(
            session_id=conversation_id,
            message=message,
            session_data=session_data
        )
        
        # Check if flow_result is None
        if flow_result is None:
            logger.error(f"[CEO_CHAT_MESSAGE] Flow result is None for conversation {conversation_id}")
            raise HTTPException(status_code=500, detail="Failed to process message - flow result is None")
        
        # Update session data
        session_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        session_data["state"] = flow_result.get("state", session_data.get("state", "gathering_requirements"))
        
        # CRITICAL FIX: Store polished prompt in session data when it's created
        if flow_result.get("polished_prompt"):
            session_data["polished_prompt"] = flow_result.get("polished_prompt")
            logger.info(f"[CEO_CHAT_MESSAGE] Stored polished prompt in session data for {conversation_id}")
        
        # Store other important data from flow result
        if flow_result.get("executive_summary"):
            session_data["executive_summary"] = flow_result.get("executive_summary")
        if flow_result.get("deliverables"):
            session_data["deliverables"] = flow_result.get("deliverables")
        
        # Prepare response
        response = {
            "conversation_id": conversation_id,
            "state": flow_result.get("state", "gathering_requirements"),
            "message": flow_result.get("response", "I'm processing your input..."),
            "requirements": flow_result.get("requirements", {}),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Include confirmation requirement flag and polished prompt info if available
        if flow_result.get("requires_confirmation"):
            response["requires_confirmation"] = True
            response["polished_prompt"] = flow_result.get("polished_prompt")
            response["executive_summary"] = flow_result.get("executive_summary")
            response["deliverables"] = flow_result.get("deliverables")
        
        # Check if requirements are complete
        if flow_result.get("state") == "requirements_complete":
            response["state"] = "requirements_complete"
            response["requirements"] = flow_result.get("requirements", {})
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@ceo_message_router.get("/api/ceo/chat/{conversation_id}/state")
async def get_chat_state(conversation_id: str):
    """Get the current state of a chat conversation"""
    
    try:
        if conversation_id not in ceo_chat_interface.active_sessions:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        session_data = ceo_chat_interface.active_sessions[conversation_id]
        
        return {
            "conversation_id": conversation_id,
            "state": session_data.get("state", ChatSessionState.GATHERING_REQUIREMENTS).value,
            "requirements": session_data.get("polished_requirements", {}),
            "questions_asked": len(session_data.get("questions_asked", [])),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@ceo_message_router.post("/api/ceo/chat/{conversation_id}/finalize")
async def finalize_requirements(conversation_id: str, request: Request):
    """Finalize requirements and create execution plan"""
    
    try:
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        if conversation_id not in ceo_chat_interface.active_sessions:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        session_data = ceo_chat_interface.active_sessions[conversation_id]
        
        log_orchestration_event(
            request_id=request_id,
            event_type="ceo_chat_finalize",
            message="Finalizing CEO requirements and creating plan",
            additional_data={"conversation_id": conversation_id}
        )
        
        # Finalize requirements
        finalization_result = await ceo_conversation_flow.finalize_requirements(
            session_id=conversation_id,
            session_data=session_data,
            request_id=request_id
        )
        
        # Log the finalization result for debugging
        logger.info(f"[CEO_CHAT_DEBUG] Finalization result: {finalization_result}")
        logger.info(f"[CEO_CHAT_DEBUG] Orchestration result in finalization: {finalization_result.get('orchestration_result', 'NOT FOUND')}")
        
        # Return the response including orchestration_result
        return {
            "conversation_id": conversation_id,
            "requirements": finalization_result.get("requirements", {}),
            "plan": finalization_result.get("plan", {}),
            "agent_plan": finalization_result.get("agent_plan", {}),
            "orchestration_result": finalization_result.get("orchestration_result", None),
            "success": finalization_result.get("success", True),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to finalize requirements: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Export router
__all__ = ["ceo_message_router"]