from fastapi import APIRouter, HTTPException, Request
from typing import List
from datetime import datetime, timezone
import uuid
import logging

from models import (
    OrchestrateRequest, 
    OrchestrationPlanResponse, 
    OrchestrationPlanStep,
    OrchestrateResponse,  # Keep for backward compatibility
    OrchestrationStatusResponse  # For status tracking
)
from data import TEAMS
from utils import (
    find_agent_by_id, 
    route_task_to_agent, 
    now_iso, 
    ceo_plan_with_llm, 
    fallback_plan
)
from logging_config import log_orchestration_event
from exceptions import AgentNotFoundException, TaskValidationException, OrchestrationException

# Create orchestration router
orchestration_router = APIRouter(prefix="/api")

# Initialize logger
logger = logging.getLogger(__name__)


@orchestration_router.post("/orchestrate", response_model=OrchestrationPlanResponse)
async def orchestrate_with_planning_only(req: OrchestrateRequest, request: Request):
    """Main orchestrate endpoint that only does planning.
    
    This endpoint returns the execution plan that the CEO agent creates,
    but doesn't execute the agents. The frontend should call individual
    agent endpoints based on this plan for real-time progress tracking.
    """
    task = req.task.strip()
    if not task:
        raise TaskValidationException("Task cannot be empty")

    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    # Log orchestration planning start
    log_orchestration_event(
        request_id=request_id,
        event_type="orchestration_planning_start",
        message=f"CEO Agent starting orchestration planning for task: {task[:100]}{'...' if len(task) > 100 else ''}",
        additional_data={
            "task_length": len(task), 
            "agent_id_requested": req.agent_id,
            "planning_mode": "plan_only",
            "workflow": "separated_endpoints"
        }
    )

    # ----- Build the plan -----
    used_llm = False
    if req.agent_id:
        agent, team_id = find_agent_by_id(req.agent_id)
        if not agent:
            log_orchestration_event(
                request_id=request_id,
                event_type="agent_not_found",
                agent_id=req.agent_id,
                message=f"Requested agent {req.agent_id} not found"
            )
            raise AgentNotFoundException(req.agent_id)
        
        log_orchestration_event(
            request_id=request_id,
            event_type="direct_agent_selection",
            agent_id=agent["id"],
            orchestration_mode="single",
            message=f"User directly selected agent: {agent['name']}"
        )
        
        plan = {
            "mode": "single",
            "rationale": f"User explicitly invoked {agent['name']}.",
            "steps": [{
                "agent_id": agent["id"],
                "agent_name": agent["name"],
                "team_id": team_id,
                "instruction": task,
            }],
        }
    else:
        log_orchestration_event(
            request_id=request_id,
            event_type="llm_planning_start",
            message="CEO Agent starting LLM-based agent selection and planning"
        )
        
        plan = await ceo_plan_with_llm(task, session_id=request_id)
        if plan:
            used_llm = True
            log_orchestration_event(
                request_id=request_id,
                event_type="llm_planning_success",
                orchestration_mode=plan.get("mode", "unknown"),
                message=f"CEO Agent LLM planning successful, mode: {plan.get('mode')}, agents: {len(plan.get('steps', []))}",
                additional_data={"plan_rationale": plan.get("rationale")}
            )
        else:
            log_orchestration_event(
                request_id=request_id,
                event_type="llm_planning_failed",
                message="CEO Agent LLM planning failed, falling back to keyword-based routing"
            )
            plan = fallback_plan(task, request_id)

    mode = plan["mode"]
    rationale = plan["rationale"]
    plan_steps = plan["steps"]
    
    # Convert plan steps to orchestration plan steps with endpoints
    orchestration_steps: List[OrchestrationPlanStep] = []
    
    for step in plan_steps:
        agent_obj, team_id_resolved = find_agent_by_id(step["agent_id"])
        if not agent_obj:
            log_orchestration_event(
                request_id=request_id,
                event_type="agent_resolution_failed",
                agent_id=step["agent_id"],
                message=f"Could not resolve agent {step['agent_id']} during planning"
            )
            continue
            
        team_name_local = next((t["name"] for t in TEAMS if t["id"] == team_id_resolved), team_id_resolved.title())
        
        # Generate endpoint path for this agent - use underscore format to match actual routes
        # The agent routes are defined with underscore format (e.g., /social_publisher)
        endpoint_path = f"/api/agents/{agent_obj['id']}"
        
        orchestration_steps.append(OrchestrationPlanStep(
            agent_id=agent_obj["id"],
            agent_name=agent_obj["name"],
            team_id=team_id_resolved,
            team_name=team_name_local,
            instruction=step["instruction"],
            endpoint=endpoint_path
        ))
    
    if not orchestration_steps:
        log_orchestration_event(
            request_id=request_id,
            event_type="no_agents_planned",
            message="No agents could be planned for this task"
        )
        raise OrchestrationException("No agent could be resolved for this task")
    
    # Log final plan details
    log_orchestration_event(
        request_id=request_id,
        event_type="orchestration_plan_complete",
        orchestration_mode=mode,
        message=f"CEO Agent orchestration plan completed with {len(orchestration_steps)} agents in {mode} mode",
        additional_data={
            "agent_ids": [s.agent_id for s in orchestration_steps],
            "rationale": rationale,
            "used_llm": used_llm,
            "total_steps": len(orchestration_steps),
            "next_action": "Frontend should call individual agent endpoints"
        }
    )

    return OrchestrationPlanResponse(
        request_id=request_id,
        task=task,
        mode=mode,
        rationale=rationale,
        steps=orchestration_steps,
        total_steps=len(orchestration_steps),
        used_llm=used_llm
    )


@orchestration_router.post("/orchestrate/plan", response_model=OrchestrationPlanResponse)
async def get_orchestration_plan(req: OrchestrateRequest, request: Request):
    """Alternative endpoint for getting orchestration plan (alias for /orchestrate).
    
    This endpoint provides the same functionality as /orchestrate for backward
    compatibility and clearer API semantics.
    """
    return await orchestrate_with_planning_only(req, request)


# Legacy endpoint for backward compatibility (full execution in single request)
@orchestration_router.post("/orchestrate/legacy", response_model=OrchestrateResponse)
async def orchestrate_legacy(req: OrchestrateRequest, request: Request):
    """Legacy orchestrate endpoint for backward compatibility.
    
    This endpoint maintains the original behavior where all agents
    are executed within a single request. For new implementations,
    use /orchestrate + individual agent endpoints.
    
    DEPRECATED: Use /orchestrate for planning + individual agent endpoints for execution.
    """
    # Import the original orchestrate function from routes.py
    from routes import orchestrate
    
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    logger.warning(f"Legacy orchestrate endpoint called for request {request_id} - consider migrating to separated workflow")
    
    log_orchestration_event(
        request_id=request_id,
        event_type="legacy_orchestrate_used",
        message="Legacy orchestrate endpoint used - all agents executed in single request",
        additional_data={
            "deprecation_warning": "Use /orchestrate + individual agent endpoints for better performance",
            "workflow": "legacy_single_request"
        }
    )
    
    # Import and call the original orchestrate function from routes.py
    from routes import orchestrate
    return await orchestrate(req, request)
