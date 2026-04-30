from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import uuid
import logging

from models import AgentExecutionRequest, AgentExecutionResponse
from data import TEAMS
from utils import find_agent_by_id, execute_task_dummy, execute_agent_real
from logging_config import log_orchestration_event
from exceptions import AgentNotFoundException, TaskValidationException

# Create agent router
agent_router = APIRouter(prefix="/api/agents")

# Initialize logger
logger = logging.getLogger(__name__)


# Define single standardized endpoint for each agent using underscore format
# This matches what orchestration returns and avoids confusion

@agent_router.post("/content_writer", response_model=AgentExecutionResponse)
async def execute_content_writer(req: AgentExecutionRequest, request: Request):
    """Execute Content Writer Agent with real LLM integration."""
    return await execute_agent("content_writer", req, request)


@agent_router.post("/social_publisher", response_model=AgentExecutionResponse)
async def execute_social_publisher(req: AgentExecutionRequest, request: Request):
    """Execute Social Media Publisher Agent with real platform integration."""
    return await execute_agent("social_publisher", req, request)


@agent_router.post("/seo_specialist", response_model=AgentExecutionResponse)
async def execute_seo_specialist(req: AgentExecutionRequest, request: Request):
    """Execute SEO Specialist Agent."""
    return await execute_agent("seo_specialist", req, request)


@agent_router.post("/ad_copywriter", response_model=AgentExecutionResponse)
async def execute_ad_copywriter(req: AgentExecutionRequest, request: Request):
    """Execute Ad Copywriter Agent."""
    return await execute_agent("ad_copywriter", req, request)


@agent_router.post("/analytics_agent", response_model=AgentExecutionResponse)
async def execute_analytics_agent(req: AgentExecutionRequest, request: Request):
    """Execute Analytics Agent."""
    return await execute_agent("analytics_agent", req, request)


@agent_router.post("/frontend_engineer", response_model=AgentExecutionResponse)
async def execute_frontend_engineer(req: AgentExecutionRequest, request: Request):
    """Execute Frontend Engineer Agent."""
    return await execute_agent("frontend_engineer", req, request)


@agent_router.post("/backend_engineer", response_model=AgentExecutionResponse)
async def execute_backend_engineer(req: AgentExecutionRequest, request: Request):
    """Execute Backend Engineer Agent."""
    return await execute_agent("backend_engineer", req, request)


@agent_router.post("/devops_agent", response_model=AgentExecutionResponse)
async def execute_devops_agent(req: AgentExecutionRequest, request: Request):
    """Execute DevOps Agent."""
    return await execute_agent("devops_agent", req, request)


@agent_router.post("/qa_agent", response_model=AgentExecutionResponse)
async def execute_qa_agent(req: AgentExecutionRequest, request: Request):
    """Execute QA Agent."""
    return await execute_agent("qa_agent", req, request)


@agent_router.post("/architect_agent", response_model=AgentExecutionResponse)
async def execute_architect_agent(req: AgentExecutionRequest, request: Request):
    """Execute Architect Agent."""
    return await execute_agent("architect_agent", req, request)


@agent_router.post("/lead_researcher", response_model=AgentExecutionResponse)
async def execute_lead_researcher(req: AgentExecutionRequest, request: Request):
    """Execute Lead Researcher Agent."""
    return await execute_agent("lead_researcher", req, request)


@agent_router.post("/outreach_agent", response_model=AgentExecutionResponse)
async def execute_outreach_agent(req: AgentExecutionRequest, request: Request):
    """Execute Outreach Agent."""
    return await execute_agent("outreach_agent", req, request)


@agent_router.post("/demo_agent", response_model=AgentExecutionResponse)
async def execute_demo_agent(req: AgentExecutionRequest, request: Request):
    """Execute Demo Agent."""
    return await execute_agent("demo_agent", req, request)


@agent_router.post("/negotiator_agent", response_model=AgentExecutionResponse)
async def execute_negotiator_agent(req: AgentExecutionRequest, request: Request):
    """Execute Negotiator Agent."""
    return await execute_agent("negotiator_agent", req, request)


@agent_router.post("/crm_agent", response_model=AgentExecutionResponse)
async def execute_crm_agent(req: AgentExecutionRequest, request: Request):
    """Execute CRM Agent."""
    return await execute_agent("crm_agent", req, request)


@agent_router.post("/user_researcher", response_model=AgentExecutionResponse)
async def execute_user_researcher(req: AgentExecutionRequest, request: Request):
    """Execute User Researcher Agent."""
    return await execute_agent("user_researcher", req, request)


@agent_router.post("/pm_agent", response_model=AgentExecutionResponse)
async def execute_pm_agent(req: AgentExecutionRequest, request: Request):
    """Execute PM Agent."""
    return await execute_agent("pm_agent", req, request)


@agent_router.post("/designer_agent", response_model=AgentExecutionResponse)
async def execute_designer_agent(req: AgentExecutionRequest, request: Request):
    """Execute Designer Agent."""
    return await execute_agent("designer_agent", req, request)


@agent_router.post("/roadmap_agent", response_model=AgentExecutionResponse)
async def execute_roadmap_agent(req: AgentExecutionRequest, request: Request):
    """Execute Roadmap Agent."""
    return await execute_agent("roadmap_agent", req, request)


@agent_router.post("/feedback_agent", response_model=AgentExecutionResponse)
async def execute_feedback_agent(req: AgentExecutionRequest, request: Request):
    """Execute Feedback Agent."""
    return await execute_agent("feedback_agent", req, request)


async def execute_agent(agent_id: str, req: AgentExecutionRequest, request: Request) -> AgentExecutionResponse:
    """Generic agent execution function.
    
    Args:
        agent_id: The ID of the agent to execute
        req: The agent execution request
        request: FastAPI request object
    
    Returns:
        AgentExecutionResponse with execution results
    """
    # Validate task
    task = req.task.strip()
    if not task:
        raise TaskValidationException("Task cannot be empty")
    
    # Generate request ID
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    started = datetime.now(timezone.utc)
    
    # Find agent
    agent, team_id = find_agent_by_id(agent_id)
    if not agent:
        logger.error(f"Agent {agent_id} not found for request {request_id}")
        raise AgentNotFoundException(agent_id)
    
    # Get team name
    team_name = next((t["name"] for t in TEAMS if t["id"] == team_id), team_id.title())
    
    # Log agent execution start
    log_orchestration_event(
        request_id=request_id,
        event_type="individual_agent_execution_start",
        agent_id=agent_id,
        message=f"Starting individual execution for {agent['name']}",
        additional_data={
            "task_preview": task[:100] + "..." if len(task) > 100 else task,
            "team_id": team_id,
            "team_name": team_name,
            "execution_mode": "individual_endpoint"
        }
    )
    
    try:
        # Execute the agent task using real agent execution
        from utils import execute_agent_real
        output = await execute_agent_real(agent_id, task, request_id)
        
        # Calculate duration
        duration_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
        
        # Log successful completion
        log_orchestration_event(
            request_id=request_id,
            event_type="individual_agent_execution_complete",
            agent_id=agent_id,
            message=f"Completed individual execution for {agent['name']} in {duration_ms}ms",
            additional_data={
                "duration_ms": duration_ms,
                "output_preview": output[:100] + "..." if len(output) > 100 else output,
                "execution_mode": "individual_endpoint",
                "success": True
            }
        )
        
        return AgentExecutionResponse(
            request_id=request_id,
            agent_id=agent_id,
            agent_name=agent["name"],
            team_id=team_id,
            team_name=team_name,
            task=task,
            output=output,
            success=True,
            duration_ms=duration_ms,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        # Calculate duration for error case
        duration_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
        
        # Log execution error
        log_orchestration_event(
            request_id=request_id,
            event_type="individual_agent_execution_error",
            agent_id=agent_id,
            message=f"Individual execution failed for {agent['name']}: {str(e)}",
            additional_data={
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "execution_mode": "individual_endpoint",
                "success": False
            }
        )
        
        logger.error(f"Agent execution failed for {agent_id}: {e}", exc_info=True)
        
        return AgentExecutionResponse(
            request_id=request_id,
            agent_id=agent_id,
            agent_name=agent["name"],
            team_id=team_id,
            team_name=team_name,
            task=task,
            output=f"Execution failed: {str(e)}",
            success=False,
            duration_ms=duration_ms,
            timestamp=datetime.now(timezone.utc).isoformat(),
            error=str(e)
        )


@agent_router.get("/list")
async def list_agents():
    """List all available agents with their endpoints."""
    agents_list = []
    
    for team in TEAMS:
        for agent in team["agents"]:
            # Single standardized endpoint using underscore format
            endpoint_path = f"/api/agents/{agent['id']}"
            agents_list.append({
                "agent_id": agent["id"],
                "agent_name": agent["name"],
                "team_id": team["id"],
                "team_name": team["name"],
                "role": agent["role"],
                "skills": agent["skills"],
                "endpoint": endpoint_path,
                "icon": agent.get("icon", "Bot"),
                "color": agent.get("color", "#000000")
            })
    
    return {
        "agents": agents_list,
        "total_agents": len(agents_list),
        "total_teams": len(TEAMS)
    }