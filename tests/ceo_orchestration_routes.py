from fastapi import APIRouter, HTTPException, Request
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
import logging
import httpx

from models import (
    OrchestrateRequest, 
    OrchestrationPlanResponse, 
    OrchestrationPlanStep,
    AgentExecutionRequest,
    AgentExecutionResponse,
    CEOOrchestrationRequest,
    CEOOrchestrationResponse,
    CEOAnalysisResponse
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

# Create CEO orchestration router
ceo_router = APIRouter(prefix="/api/ceo")

# Initialize logger
logger = logging.getLogger(__name__)

# Base URL for agent endpoints
AGENT_BASE_URL = "http://localhost:8000"


@ceo_router.post("/orchestrate", response_model=CEOOrchestrationResponse)
async def ceo_orchestrate_workflow(req: CEOOrchestrationRequest, request: Request):
    """CEO orchestration workflow that manages agent execution and delegation.
    
    This endpoint:
    1. Creates an execution plan
    2. Executes agents sequentially
    3. Analyzes each agent's output
    4. Delegates to next agent with proper formatting
    5. Returns final aggregated results
    """
    task = req.task.strip()
    if not task:
        raise TaskValidationException("Task cannot be empty")

    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    started = datetime.now(timezone.utc)
    
    # Log CEO orchestration start
    log_orchestration_event(
        request_id=request_id,
        event_type="ceo_orchestration_start",
        message=f"CEO Agent starting orchestration workflow for task: {task[:100]}{'...' if len(task) > 100 else ''}",
        additional_data={
            "task_length": len(task), 
            "workflow": "ceo_mediated",
            "mode": "sequential_with_analysis"
        }
    )

    # Step 1: Create execution plan
    try:
        plan = await ceo_plan_with_llm(task, session_id=request_id)
        if not plan:
            plan = fallback_plan(task, request_id)
        
        log_orchestration_event(
            request_id=request_id,
            event_type="ceo_plan_created",
            message=f"CEO created execution plan with {len(plan.get('steps', []))} agents",
            additional_data={
                "mode": plan.get("mode"),
                "rationale": plan.get("rationale"),
                "agent_count": len(plan.get("steps", []))
            }
        )
    except Exception as e:
        logger.error(f"CEO planning failed: {e}")
        raise OrchestrationException(f"CEO planning failed: {str(e)}")

    # Step 2: Execute agents sequentially with CEO analysis
    agent_results = []
    current_context = task  # Start with original task
    
    for i, step in enumerate(plan.get("steps", [])):
        agent_id = step["agent_id"]
        instruction = step["instruction"]
        
        # Find agent details
        agent, team_id = find_agent_by_id(agent_id)
        if not agent:
            logger.error(f"Agent {agent_id} not found during execution")
            continue
            
        team_name = next((t["name"] for t in TEAMS if t["id"] == team_id), team_id.title())
        
        log_orchestration_event(
            request_id=request_id,
            event_type="ceo_agent_execution_start",
            agent_id=agent_id,
            message=f"CEO delegating to {agent['name']} (step {i+1}/{len(plan['steps'])})",
            additional_data={
                "step_number": i + 1,
                "total_steps": len(plan["steps"]),
                "instruction": instruction[:100] + "..." if len(instruction) > 100 else instruction
            }
        )
        
        # Execute agent
        try:
            agent_result = await execute_agent_via_endpoint(agent_id, current_context, request_id)
            
            # Log agent completion
            log_orchestration_event(
                request_id=request_id,
                event_type="ceo_agent_execution_complete",
                agent_id=agent_id,
                message=f"Agent {agent['name']} completed execution",
                additional_data={
                    "success": agent_result.success,
                    "duration_ms": agent_result.duration_ms,
                    "output_preview": agent_result.output[:100] + "..." if len(agent_result.output) > 100 else agent_result.output
                }
            )
            
            # CEO analyzes the result and prepares context for next agent
            if i < len(plan["steps"]) - 1:  # Not the last agent
                next_agent_id = plan["steps"][i + 1]["agent_id"]
                analyzed_context = await ceo_analyze_and_prepare_context(
                    agent_result, next_agent_id, task, request_id
                )
                current_context = analyzed_context
                
                log_orchestration_event(
                    request_id=request_id,
                    event_type="ceo_context_analysis",
                    agent_id=agent_id,
                    message=f"CEO analyzed {agent['name']} output and prepared context for next agent",
                    additional_data={
                        "next_agent_id": next_agent_id,
                        "context_length": len(analyzed_context)
                    }
                )
            
            agent_results.append(agent_result)
            
        except Exception as e:
            logger.error(f"Agent {agent_id} execution failed: {e}")
            
            # Create error result
            error_result = AgentExecutionResponse(
                request_id=request_id,
                agent_id=agent_id,
                agent_name=agent["name"],
                team_id=team_id,
                team_name=team_name,
                task=current_context,
                output=f"Execution failed: {str(e)}",
                success=False,
                duration_ms=0,
                timestamp=datetime.now(timezone.utc).isoformat(),
                error=str(e)
            )
            agent_results.append(error_result)
    
    # Calculate total duration
    total_duration_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    
    # Generate final CEO analysis
    final_output = await ceo_generate_final_analysis(agent_results, task, request_id)
    
    log_orchestration_event(
        request_id=request_id,
        event_type="ceo_orchestration_complete",
        message=f"CEO orchestration workflow completed with {len(agent_results)} agents",
        additional_data={
            "total_duration_ms": total_duration_ms,
            "successful_agents": sum(1 for r in agent_results if r.success),
            "failed_agents": sum(1 for r in agent_results if not r.success),
            "final_output_length": len(final_output)
        }
    )
    
    return CEOOrchestrationResponse(
        request_id=request_id,
        task=task,
        mode=plan.get("mode", "sequential"),
        rationale=plan.get("rationale", "CEO-mediated workflow"),
        agent_results=agent_results,
        final_output=final_output,
        total_duration_ms=total_duration_ms,
        timestamp=datetime.now(timezone.utc).isoformat(),
        success=any(r.success for r in agent_results)
    )


async def execute_agent_via_endpoint(agent_id: str, task: str, request_id: str) -> AgentExecutionResponse:
    """Execute an agent via its individual endpoint."""
    endpoint_path = f"/api/agents/{agent_id.replace('_', '-')}"
    url = f"{AGENT_BASE_URL}{endpoint_path}"
    
    payload = {
        "task": task
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            result_data = response.json()
            return AgentExecutionResponse(**result_data)
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling agent {agent_id}: {e}")
            raise Exception(f"Failed to call agent {agent_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error calling agent {agent_id}: {e}")
            raise Exception(f"Agent {agent_id} execution failed: {str(e)}")


async def ceo_analyze_and_prepare_context(agent_result: AgentExecutionResponse, next_agent_id: str, original_task: str, request_id: str) -> str:
    """CEO analyzes agent output and prepares context for next agent."""
    
    # Find next agent details
    next_agent, _ = find_agent_by_id(next_agent_id)
    if not next_agent:
        return agent_result.output
    
    # CEO analysis prompt based on agent types
    analysis_prompt = f"""
As the CEO, I need to analyze the output from {agent_result.agent_name} and prepare appropriate input for {next_agent['name']}.

Original Task: {original_task}

{agent_result.agent_name} Output:
{agent_result.output}

Next Agent: {next_agent['name']}
Next Agent Role: {next_agent['role']}
Next Agent Skills: {', '.join(next_agent['skills'])}

Please analyze the output and provide the appropriate input/context for {next_agent['name']} to continue the workflow effectively. 

If {agent_result.agent_name} created content and {next_agent['name']} is a Social Media Publisher, provide the content along with posting instructions.
If the workflow involves content creation followed by publishing, ensure the content is properly formatted for the publishing agent.

Provide only the task/context for the next agent, not explanations:
"""
    
    try:
        # Use LLM to analyze and prepare context
        from ai_service import ai_service
        analyzed_context = await ai_service.generate_content(analysis_prompt, request_id)
        
        log_orchestration_event(
            request_id=request_id,
            event_type="ceo_context_prepared",
            agent_id=next_agent_id,
            message=f"CEO prepared context for {next_agent['name']}",
            additional_data={
                "previous_agent": agent_result.agent_name,
                "context_length": len(analyzed_context)
            }
        )
        
        return analyzed_context
        
    except Exception as e:
        logger.error(f"CEO context analysis failed: {e}")
        # Fallback: use original output with basic formatting
        return f"Based on the previous work by {agent_result.agent_name}:\n\n{agent_result.output}\n\nPlease proceed with your task."


async def ceo_generate_final_analysis(agent_results: List[AgentExecutionResponse], original_task: str, request_id: str) -> str:
    """CEO generates final analysis combining all agent outputs."""
    
    successful_results = [r for r in agent_results if r.success]
    
    if not successful_results:
        return "All agents failed to complete their tasks. Please review the errors and try again."
    
    # Create summary of all agent outputs
    summary_prompt = f"""
As the CEO, I need to provide a final summary of the completed workflow.

Original Task: {original_task}

Agent Execution Results:
"""
    
    for i, result in enumerate(agent_results, 1):
        status = "✅ SUCCESS" if result.success else "❌ FAILED"
        summary_prompt += f"""
{i}. {result.agent_name} ({result.team_name}) - {status}
   Duration: {result.duration_ms}ms
   Output: {result.output[:200]}{'...' if len(result.output) > 200 else ''}
   
"""
    
    summary_prompt += """
Please provide a concise executive summary of the workflow completion, highlighting:
1. What was accomplished
2. Key outputs from each agent
3. Overall success status
4. Any recommendations for follow-up actions

Provide a professional CEO-level summary:
"""
    
    try:
        from ai_service import ai_service
        final_analysis = await ai_service.generate_content(summary_prompt, request_id)
        
        log_orchestration_event(
            request_id=request_id,
            event_type="ceo_final_analysis_generated",
            message="CEO generated final workflow analysis",
            additional_data={
                "analysis_length": len(final_analysis),
                "successful_agents": len(successful_results),
                "total_agents": len(agent_results)
            }
        )
        
        return final_analysis
        
    except Exception as e:
        logger.error(f"CEO final analysis failed: {e}")
        # Fallback summary
        return f"Workflow completed with {len(successful_results)}/{len(agent_results)} agents successful. Please review individual agent outputs for details."


@ceo_router.post("/analyze", response_model=CEOAnalysisResponse)
async def ceo_analyze_agent_output(req: Dict[str, Any], request: Request):
    """CEO analyzes a specific agent output and provides recommendations."""
    
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    agent_output = req.get("agent_output", "")
    agent_name = req.get("agent_name", "Unknown Agent")
    original_task = req.get("original_task", "")
    next_agent = req.get("next_agent", "")
    
    analysis_prompt = f"""
As the CEO, analyze this agent output and provide strategic recommendations.

Original Task: {original_task}
Agent: {agent_name}
Output: {agent_output}
Next Agent: {next_agent}

Provide analysis including:
1. Quality assessment
2. Alignment with original task
3. Recommendations for improvement
4. Context for next agent (if applicable)
"""
    
    try:
        from ai_service import ai_service
        analysis = await ai_service.generate_content(analysis_prompt, request_id)
        
        return CEOAnalysisResponse(
            request_id=request_id,
            agent_name=agent_name,
            analysis=analysis,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        logger.error(f"CEO analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"CEO analysis failed: {str(e)}")