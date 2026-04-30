from fastapi import APIRouter, Request
from typing import List
from datetime import datetime, timezone
import uuid

from ..core.models import OrchestrateRequest, OrchestrateResponse, StepLog, AgentRun
from ..core.data import TEAMS, LOCKED_TEAMS
from ..core.utils import (
    find_agent_by_id, 
    route_task_to_agent, 
    now_iso, 
    ceo_plan_with_llm, 
    fallback_plan, 
    execute_task_dummy
)
from ..core.logging_config import log_orchestration_event
from ..core.exceptions import AgentNotFoundException, TaskValidationException, OrchestrationException
from .ai_routes import ai_router

api_router = APIRouter(prefix="/api")

# Include AI routes
api_router.include_router(ai_router)


@api_router.get("/")
async def root():
    return {"message": "AI Startup System online", "phase": 1}


@api_router.get("/teams")
async def get_teams():
    return {"teams": TEAMS, "locked_teams": LOCKED_TEAMS}


@api_router.post("/orchestrate/execute-all", response_model=OrchestrateResponse)
async def orchestrate(req: OrchestrateRequest, request: Request):
    task = req.task.strip()
    if not task:
        raise TaskValidationException("Task cannot be empty")

    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    started = datetime.now(timezone.utc)
    steps: List[StepLog] = []
    
    # Log orchestration start with task details
    log_orchestration_event(
        request_id=request_id,
        event_type="task_received",
        message=f"Task received: {task[:100]}{'...' if len(task) > 100 else ''}",
        additional_data={"task_length": len(task), "agent_id_requested": req.agent_id}
    )

    steps.append(StepLog(
        actor="CEO",
        message=f"Received directive: \"{task[:140]}\"",
        status="info",
        timestamp=now_iso(),
    ))

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
        steps.append(StepLog(
            actor="CEO",
            message="Consulting Claude · drafting multi-agent plan…",
            status="thinking",
            timestamp=now_iso(),
        ))
        
        log_orchestration_event(
            request_id=request_id,
            event_type="llm_planning_start",
            message="Starting LLM-based agent selection and planning"
        )
        
        plan = await ceo_plan_with_llm(task, session_id=request_id)
        if plan:
            used_llm = True
            log_orchestration_event(
                request_id=request_id,
                event_type="llm_planning_success",
                orchestration_mode=plan.get("mode", "unknown"),
                message=f"LLM planning successful, mode: {plan.get('mode')}, agents: {len(plan.get('steps', []))}",
                additional_data={"plan_rationale": plan.get("rationale")}
            )
        else:
            log_orchestration_event(
                request_id=request_id,
                event_type="llm_planning_failed",
                message="LLM planning failed, falling back to keyword-based routing"
            )
            plan = fallback_plan(task, request_id)

    mode = plan["mode"]
    rationale = plan["rationale"]
    plan_steps = plan["steps"]
    
    # Store orchestration metadata in request state for middleware
    request.state.orchestration_mode = mode
    request.state.agent_count = len(plan_steps)

    steps.append(StepLog(
        actor="CEO",
        message=f"Plan ready · mode={mode} · {len(plan_steps)} agent(s) · {rationale}",
        status="info",
        timestamp=now_iso(),
    ))
    
    # Log final plan details
    log_orchestration_event(
        request_id=request_id,
        event_type="plan_finalized",
        orchestration_mode=mode,
        message=f"Plan finalized with {len(plan_steps)} agents in {mode} mode",
        additional_data={
            "agent_ids": [s["agent_id"] for s in plan_steps],
            "rationale": rationale,
            "used_llm": used_llm
        }
    )

    # ----- Execute each agent in plan order -----
    agent_runs: List[AgentRun] = []
    for i, s in enumerate(plan_steps):
        agent_obj, team_id_resolved = find_agent_by_id(s["agent_id"])
        if not agent_obj:
            log_orchestration_event(
                request_id=request_id,
                event_type="agent_resolution_failed",
                agent_id=s["agent_id"],
                message=f"Could not resolve agent {s['agent_id']} during execution"
            )
            continue
        team_name_local = next((t["name"] for t in TEAMS if t["id"] == team_id_resolved), team_id_resolved.title())

        steps.append(StepLog(
            actor="CEO",
            message=f"→ Handing off to {agent_obj['name']} ({team_name_local}): {s['instruction']}",
            status="info",
            timestamp=now_iso(),
        ))
        steps.append(StepLog(
            actor=agent_obj["name"],
            message="Acknowledged. Working on it…",
            status="working",
            timestamp=now_iso(),
        ))
        
        log_orchestration_event(
            request_id=request_id,
            event_type="agent_handoff",
            agent_id=agent_obj["id"],
            orchestration_mode=mode,
            message=f"Handing off to {agent_obj['name']} (step {i+1}/{len(plan_steps)})",
            additional_data={"instruction": s["instruction"], "team_name": team_name_local}
        )
        
        out = await execute_task_dummy(agent_obj, s["instruction"], request_id)
        
        steps.append(StepLog(
            actor=agent_obj["name"],
            message="Output ready. Delivering to CEO.",
            status="success",
            timestamp=now_iso(),
        ))
        agent_runs.append(AgentRun(
            agent_id=agent_obj["id"],
            agent_name=agent_obj["name"],
            team_id=team_id_resolved,
            team_name=team_name_local,
            instruction=s["instruction"],
            output=out,
        ))

    if not agent_runs:
        log_orchestration_event(
            request_id=request_id,
            event_type="no_agents_executed",
            message="No agents could be executed for this task"
        )
        raise OrchestrationException("No agent could be resolved for this task")

    steps.append(StepLog(
        actor="CEO",
        message="All agents reported back. Mission complete.",
        status="success",
        timestamp=now_iso(),
    ))
    
    duration_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    primary = agent_runs[0]
    
    # Log orchestration completion
    log_orchestration_event(
        request_id=request_id,
        event_type="orchestration_complete",
        orchestration_mode=mode,
        message=f"Orchestration completed successfully in {duration_ms}ms",
        additional_data={
            "duration_ms": duration_ms,
            "agents_executed": len(agent_runs),
            "primary_agent": primary.agent_id,
            "used_llm": used_llm
        }
    )

    return OrchestrateResponse(
        request_id=request_id,
        task=task,
        mode=mode,
        rationale=rationale,
        chosen_agent_id=primary.agent_id,
        chosen_agent_name=primary.agent_name,
        team_id=primary.team_id,
        team_name=primary.team_name,
        agent_runs=agent_runs,
        steps=steps,
        output=primary.output,
        duration_ms=duration_ms,
        used_llm=used_llm,
    )