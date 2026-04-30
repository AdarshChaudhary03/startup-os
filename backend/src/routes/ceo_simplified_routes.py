"""Simplified CEO Agent Routes

This module provides the API routes for the simplified CEO agent flow.
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
import logging
import uuid

from src.agents.ceo.ceo_simplified_flow import simplified_ceo_agent
from src.core.models import OrchestrateRequest

# Create router
ceo_simplified_router = APIRouter(prefix="/api/ceo/simplified")

# Initialize logger
logger = logging.getLogger(__name__)


@ceo_simplified_router.post("/process")
async def process_task_simplified(request: Request, task_request: Dict[str, Any]):
    """Process a task using the simplified CEO agent flow
    
    This endpoint handles the complete simplified flow:
    1. Clarify requirements (would integrate with chat)
    2. Format requirements into polished prompt
    3. Get orchestration plan
    4. Execute agents sequentially
    5. Manage inter-agent communication
    """
    task = task_request.get("task", "").strip()
    if not task:
        raise HTTPException(status_code=400, detail="Task cannot be empty")
    
    session_id = task_request.get("session_id", str(uuid.uuid4()))
    request_id = getattr(request.state, 'request_id', session_id)
    
    logger.info(f"[CEO_SIMPLIFIED_ROUTE] Processing task for session {session_id}")
    
    try:
        # Process the task using simplified flow
        result = await simplified_ceo_agent.process_user_task(
            task=task,
            session_id=session_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"[CEO_SIMPLIFIED_ROUTE] Error processing task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@ceo_simplified_router.post("/orchestrate")
async def orchestrate_simplified(request: Request, orchestrate_request: OrchestrateRequest):
    """Get orchestration plan using simplified flow
    
    This endpoint specifically handles getting the orchestration plan
    after requirements have been clarified and formatted.
    """
    task = orchestrate_request.task.strip()
    if not task:
        raise HTTPException(status_code=400, detail="Task cannot be empty")
    
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    logger.info(f"[CEO_SIMPLIFIED_ROUTE] Getting orchestration plan for task")
    
    try:
        # Assume task is already a polished prompt
        orchestration_plan = await simplified_ceo_agent.get_orchestration_plan(
            polished_requirements=task,
            session_id=request_id
        )
        
        return orchestration_plan
        
    except Exception as e:
        logger.error(f"[CEO_SIMPLIFIED_ROUTE] Error getting orchestration plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@ceo_simplified_router.post("/execute-agent")
async def execute_single_agent(request: Request, agent_request: Dict[str, Any]):
    """Execute a single agent with the provided payload
    
    This endpoint allows executing individual agents as part of the
    simplified flow, enabling the CEO to delegate tasks sequentially.
    """
    agent_id = agent_request.get("agent_id")
    agent_name = agent_request.get("agent_name")
    endpoint = agent_request.get("endpoint")
    payload = agent_request.get("payload", {})
    session_id = agent_request.get("session_id", str(uuid.uuid4()))
    
    if not all([agent_id, agent_name, endpoint, payload]):
        raise HTTPException(
            status_code=400,
            detail="Missing required fields: agent_id, agent_name, endpoint, payload"
        )
    
    logger.info(f"[CEO_SIMPLIFIED_ROUTE] Executing agent {agent_name} for session {session_id}")
    
    try:
        # Execute the agent
        result = await simplified_ceo_agent.execute_agent(
            agent_id=agent_id,
            agent_name=agent_name,
            endpoint=endpoint,
            payload=payload,
            session_id=session_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"[CEO_SIMPLIFIED_ROUTE] Error executing agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@ceo_simplified_router.get("/agent-payload-format/{agent_id}")
async def get_agent_payload_format(agent_id: str):
    """Get the expected payload format for a specific agent
    
    This endpoint returns the payload structure that the CEO agent
    should use when calling a specific agent.
    """
    logger.info(f"[CEO_SIMPLIFIED_ROUTE] Getting payload format for agent {agent_id}")
    
    payload_format = simplified_ceo_agent.get_agent_payload_format(agent_id)
    
    if not payload_format:
        raise HTTPException(
            status_code=404,
            detail=f"Payload format not found for agent {agent_id}"
        )
    
    return {
        "agent_id": agent_id,
        "payload_format": payload_format
    }


@ceo_simplified_router.post("/execute-plan")
async def execute_orchestration_plan(request: Request, execution_request: Dict[str, Any]):
    """Execute a complete orchestration plan sequentially
    
    This endpoint takes an orchestration plan and executes all agents
    in sequence, managing inter-agent communication.
    """
    orchestration_plan = execution_request.get("orchestration_plan")
    polished_requirements = execution_request.get("polished_requirements", "")
    session_id = execution_request.get("session_id", str(uuid.uuid4()))
    
    if not orchestration_plan:
        raise HTTPException(
            status_code=400,
            detail="Missing orchestration_plan"
        )
    
    logger.info(f"[CEO_SIMPLIFIED_ROUTE] Executing orchestration plan for session {session_id}")
    
    try:
        # Execute the plan sequentially
        execution_results = await simplified_ceo_agent.execute_plan_sequentially(
            orchestration_plan=orchestration_plan,
            polished_requirements=polished_requirements,
            session_id=session_id
        )
        
        return {
            "session_id": session_id,
            "execution_results": execution_results,
            "total_agents_executed": len(execution_results),
            "success": all(r.get("success", False) for r in execution_results)
        }
        
    except Exception as e:
        logger.error(f"[CEO_SIMPLIFIED_ROUTE] Error executing orchestration plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))
