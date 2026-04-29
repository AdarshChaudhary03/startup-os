import asyncio
import random
import re
import json as json_lib
import logging
from typing import Dict, Optional
from datetime import datetime, timezone
from google.genai import types

from config import gemini_client  # Deprecated - use ai_service instead
from data import TEAMS, DUMMY_OUTPUTS
from logging_config import log_orchestration_event


def route_task_to_agent(task: str):
    """CEO logic: pick the most relevant agent across all teams based on keyword scoring.
    LLM-ready: replace body with an LLM call returning agent_id + team_id.
    Returns (agent_dict, team_id).
    """
    task_lower = task.lower()
    
    # Special routing logic for content creation vs publishing
    content_creation_keywords = ['write', 'create', 'caption', 'content', 'copy', 'text', 'blog', 'article']
    publishing_keywords = ['schedule', 'publish', 'post timing', 'distribution']
    
    # Check if this is a content creation task
    is_content_creation = any(keyword in task_lower for keyword in content_creation_keywords)
    is_publishing = any(keyword in task_lower for keyword in publishing_keywords)
    
    # Force Content Writer for content creation tasks
    if is_content_creation and not is_publishing:
        for team in TEAMS:
            for agent in team["agents"]:
                if agent["id"] == "content_writer":
                    return agent, team["id"]
    
    # Original keyword scoring logic for other tasks
    best_agent = TEAMS[0]["agents"][0]
    best_team_id = TEAMS[0]["id"]
    best_score = -1
    for team in TEAMS:
        for agent in team["agents"]:
            score = sum(1 for kw in agent["skills"] if kw in task_lower)
            if score > best_score:
                best_score = score
                best_agent = agent
                best_team_id = team["id"]
    return best_agent, best_team_id


def find_agent_by_id(agent_id: str):
    """Find agent and team_id by agent_id."""
    for team in TEAMS:
        for agent in team["agents"]:
            if agent["id"] == agent_id:
                return agent, team["id"]
    return None, None


async def execute_task_dummy(agent: Dict, task: str, request_id: str) -> str:
    """Agent execution with LLM integration for Content Writer and Social Media Publisher Agents.
    
    This function is now deprecated for individual agent execution.
    Individual agents should be called through their dedicated endpoints.
    This function is kept for backward compatibility with orchestration.
    """
    
    # Log agent execution start
    log_orchestration_event(
        request_id=request_id,
        event_type="agent_execution_start",
        agent_id=agent["id"],
        message=f"Starting execution for agent {agent['name']}",
        additional_data={"task_preview": task[:50] + "..." if len(task) > 50 else task}
    )
    
    # For orchestration, all agents should now use dummy outputs
    # Real agent execution happens through individual agent endpoints
    await asyncio.sleep(0.3)
    output = random.choice(DUMMY_OUTPUTS.get(agent["id"], ["Task completed successfully."]))
    
    # Log dummy execution completion
    log_orchestration_event(
        request_id=request_id,
        event_type="agent_execution_complete",
        agent_id=agent["id"],
        message=f"Completed dummy execution for agent {agent['name']} (orchestration mode)",
        additional_data={
            "output_preview": output[:100] + "..." if len(output) > 100 else output,
            "execution_type": "dummy_data_orchestration"
        }
    )
    
    return output


async def execute_agent_real(agent_id: str, task: str, request_id: str) -> str:
    """Real agent execution for individual agent endpoints.
    
    This function handles the actual LLM integration for Content Writer and Social Media Publisher.
    Used by individual agent endpoints, not by orchestration.
    """
    
    # Find the agent
    agent, team_id = find_agent_by_id(agent_id)
    if not agent:
        raise ValueError(f"Agent {agent_id} not found")
    
    # Log agent execution start
    log_orchestration_event(
        request_id=request_id,
        event_type="real_agent_execution_start",
        agent_id=agent["id"],
        message=f"Starting real execution for agent {agent['name']}",
        additional_data={"task_preview": task[:50] + "..." if len(task) > 50 else task}
    )
    
    # Check if this is the Content Writer Agent - use Content Writer v2 Main Agent
    if agent["id"] == "content_writer":
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Content Writer v2 Main Agent detected for request {request_id}")
            
            # Import Content Writer v2 Main Agent
            from content_writer_v2.main_agent import ContentWriterMainAgent
            from content_writer_v2.config import DEFAULT_CONFIG
            
            # Create and initialize the main agent
            main_agent = ContentWriterMainAgent(DEFAULT_CONFIG)
            await main_agent.initialize()
            
            # Generate content using the main agent with auto-detection
            result = await main_agent.generate_content(
                task=task,
                request_id=request_id
            )
            
            # Extract the actual content from the result
            output = result.get("content", "Content generation completed successfully.")
            
            # Log LLM-powered execution completion
            log_orchestration_event(
                request_id=request_id,
                event_type="real_agent_execution_complete",
                agent_id=agent["id"],
                message=f"Completed Content Writer v2 execution for agent {agent['name']}",
                additional_data={
                    "output_preview": output[:100] + "..." if len(output) > 100 else output,
                    "execution_type": "content_writer_v2",
                    "category_used": result.get("category_used", "auto"),
                    "sub_agent_used": result.get("sub_agent_used", "unknown"),
                    "content_length": len(output)
                }
            )
            
            return output
            
        except Exception as e:
            # Log error and re-raise for proper error handling
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Content Writer v2 execution failed for request {request_id}: {e}", exc_info=True)
            log_orchestration_event(
                request_id=request_id,
                event_type="real_agent_execution_error",
                agent_id=agent["id"],
                message=f"Content Writer v2 execution failed: {str(e)}",
                additional_data={"error_type": type(e).__name__, "full_error": str(e)}
            )
            raise e
    
    # Check if this is the Social Media Publisher Agent - use Social Media Publisher Main Agent
    elif agent["id"] == "social_publisher":
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Social Media Publisher Main Agent detected for request {request_id}")
            
            # Import Social Media Publisher Main Agent
            from social_media_publisher.main_agent import SocialMediaPublisherMainAgent
            from social_media_publisher.config import DEFAULT_CONFIG
            
            # Create and initialize the main agent
            main_agent = SocialMediaPublisherMainAgent(DEFAULT_CONFIG)
            await main_agent.initialize()
            
            # Publish content using the main agent with auto-detection
            result = await main_agent.publish_content(
                content=task,  # Task contains the content to publish
                request_id=request_id
            )
            
            # Format the output based on publishing results
            if result.get("success", False):
                platforms_published = result.get("platforms_published", [])
                successful_count = result.get("successful_platforms", 0)
                
                if successful_count == 1:
                    platform = platforms_published[0]
                    platform_result = result.get("results", {}).get(platform, {})
                    post_url = platform_result.get("url", "")
                    output = f"Successfully published to {platform.title()}. {post_url if post_url else 'Content live on platform.'}"
                else:
                    output = f"Successfully published to {successful_count} platforms: {', '.join([p.title() for p in platforms_published])}. Multi-platform distribution completed."
            else:
                failed_platforms = result.get("platforms_failed", [])
                if failed_platforms:
                    output = f"Publishing failed for platforms: {', '.join(failed_platforms)}. Please check platform configurations."
                else:
                    output = "Publishing completed with mixed results. Check individual platform statuses."
            
            # Log LLM-powered execution completion
            log_orchestration_event(
                request_id=request_id,
                event_type="real_agent_execution_complete",
                agent_id=agent["id"],
                message=f"Completed Social Media Publisher execution for agent {agent['name']}",
                additional_data={
                    "output_preview": output[:100] + "..." if len(output) > 100 else output,
                    "execution_type": "social_media_publisher",
                    "platforms_published": result.get("platforms_published", []),
                    "successful_platforms": result.get("successful_platforms", 0),
                    "failed_platforms": result.get("failed_platforms", 0),
                    "total_reach": result.get("aggregated_metrics", {}).get("total_estimated_reach", 0)
                }
            )
            
            return output
            
        except Exception as e:
            # Log error and re-raise for proper error handling
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Social Media Publisher execution failed for request {request_id}: {e}", exc_info=True)
            log_orchestration_event(
                request_id=request_id,
                event_type="real_agent_execution_error",
                agent_id=agent["id"],
                message=f"Social Media Publisher execution failed: {str(e)}",
                additional_data={"error_type": type(e).__name__, "full_error": str(e)}
            )
            raise e
    
    # For all other agents, use dummy data
    await asyncio.sleep(0.3)
    output = random.choice(DUMMY_OUTPUTS.get(agent_id, ["Task completed successfully."]))
    
    # Log dummy execution completion
    log_orchestration_event(
        request_id=request_id,
        event_type="real_agent_execution_complete",
        agent_id=agent_id,
        message=f"Completed dummy execution for agent {agent['name']} (not yet implemented)",
        additional_data={
            "output_preview": output[:100] + "..." if len(output) > 100 else output,
            "execution_type": "dummy_data_individual_endpoint"
        }
    )
    
    return output


def build_agent_catalog() -> str:
    """Build a text catalog of all available agents for LLM planning."""
    lines = []
    for team in TEAMS:
        lines.append(f"\n## {team['name']} Team — {team['tagline']}")
        for a in team["agents"]:
            skills = ", ".join(a["skills"])
            lines.append(f"  - id: {a['id']}  | {a['name']} — {a['role']} | skills: {skills}")
    return "\n".join(lines)


CEO_SYSTEM_PROMPT = """You are the CEO of an AI startup. You orchestrate a roster of 20 specialist agents across 4 teams.

Your job: receive a user directive and produce a plan that decides which agent(s) handle it, and how.

ROSTER:
{catalog}

RULES:
1. Choose the smallest competent set of agents (1, 2, or at most 3 agents).
2. Pick "mode":
   - "single"      — one agent handles it.
   - "sequential"  — agent 1's output feeds agent 2 (chain). Use when handoff is needed (e.g. research → write → publish).
   - "parallel"    — multiple agents work on independent slices of the task at the same time.
3. Use agents from any team. Cross-team plans are encouraged when the task naturally spans domains.
4. For each step, write a short, specific instruction for that agent (one sentence, imperative).
5. The "rationale" should be ONE short sentence explaining your routing decision.

IMPORTANT AGENT SELECTION GUIDELINES:
- Content Writer: Use for ALL content creation tasks (writing, captions, copy, text generation)
- Social Media Publisher: Use ONLY for scheduling, publishing, and distribution tasks
- For content creation requests (like "write a caption", "create content", "write copy"), ALWAYS choose Content Writer
- For publishing/scheduling requests (like "schedule post", "publish content"), choose Social Media Publisher

OUTPUT REQUIREMENT — STRICT JSON ONLY. No markdown fences. No prose. Exactly this shape:
{{
  "mode": "single|sequential|parallel",
  "rationale": "<one sentence>",
  "steps": [
    {{ "agent_id": "<one of the roster ids>", "instruction": "<short imperative instruction>" }}
  ]
}}

Only use agent_id values that exist in the roster above. If unsure, default to mode "single" with the single best-fit agent."""


def _extract_json(text: str) -> Optional[dict]:
    """Extract JSON object from LLM response — strips markdown fences and prose."""
    if not text:
        return None
    # Strip ```json ... ``` fences if present
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fence:
        candidate = fence.group(1)
    else:
        # Find first { ... } block
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return None
        candidate = m.group(0)
    try:
        return json_lib.loads(candidate)
    except Exception:
        return None


def _validate_plan(plan: dict) -> Optional[dict]:
    """Validate and clean the plan dict. Returns cleaned plan or None if invalid."""
    if not isinstance(plan, dict):
        return None
    mode = plan.get("mode") or "single"
    if mode not in ("single", "sequential", "parallel"):
        mode = "single"
    rationale = (plan.get("rationale") or "").strip() or "Best-fit specialist selected."
    raw_steps = plan.get("steps") or []
    if not isinstance(raw_steps, list) or not raw_steps:
        return None
    cleaned_steps = []
    for s in raw_steps[:3]:  # cap at 3 agents
        if not isinstance(s, dict):
            continue
        agent_id = s.get("agent_id")
        instruction = (s.get("instruction") or "").strip()
        agent, team_id = find_agent_by_id(agent_id) if agent_id else (None, None)
        if not agent:
            continue
        if not instruction:
            instruction = f"Handle this task: {agent['role']}."
        cleaned_steps.append({
            "agent_id": agent["id"],
            "agent_name": agent["name"],
            "team_id": team_id,
            "instruction": instruction,
        })
    if not cleaned_steps:
        return None
    return {"mode": mode, "rationale": rationale, "steps": cleaned_steps}


async def ceo_plan_with_llm(task: str, session_id: str) -> Optional[dict]:
    """Legacy function for backward compatibility.
    
    This function now delegates to the new AI service architecture.
    Use ceo_plan_with_llm_new from ai_startup module for new implementations.
    """
    # Import here to avoid circular imports
    from ai_startup import ceo_plan_with_llm_new
    
    # Try new AI service first
    try:
        return await ceo_plan_with_llm_new(task, session_id)
    except Exception as e:
        logging.warning(f"New AI service failed, falling back to legacy Gemini: {e}")
    
    # Fallback to legacy Gemini implementation
    if not gemini_client:
        log_orchestration_event(
            request_id=session_id,
            event_type="llm_unavailable",
            message="No AI providers available for planning"
        )
        return None
    try:
        catalog = build_agent_catalog()
        system_message = CEO_SYSTEM_PROMPT.format(catalog=catalog)
        
        # Combine system message and user directive
        prompt = f"{system_message}\n\nUSER DIRECTIVE: {task}\n\nReturn the JSON plan now."
        
        # Generate response using the new google.genai API
        response = await asyncio.to_thread(
            gemini_client.models.generate_content,
            model='gemini-2.5-pro',
            contents=types.Content(
                parts=[types.Part(text=prompt)]
            )
        )
        
        raw = response.candidates[0].content.parts[0].text
        
        plan = _extract_json(raw if isinstance(raw, str) else str(raw))
        if not plan:
            log_orchestration_event(
                request_id=session_id,
                event_type="llm_json_parse_failed",
                message="Failed to parse JSON from LLM response",
                additional_data={"raw_response_preview": str(raw)[:200]}
            )
            logging.warning("CEO LLM: failed to parse JSON. Raw: %s", str(raw)[:300])
            return None
        cleaned = _validate_plan(plan)
        if not cleaned:
            log_orchestration_event(
                request_id=session_id,
                event_type="llm_plan_validation_failed",
                message="LLM plan failed validation",
                additional_data={"raw_plan": plan}
            )
            logging.warning("CEO LLM: invalid plan after validation: %s", plan)
            return None
        return cleaned
    except Exception as e:
        log_orchestration_event(
            request_id=session_id,
            event_type="llm_call_error",
            message=f"LLM call failed: {str(e)}",
            additional_data={"error_type": type(e).__name__}
        )
        logging.exception("CEO LLM call failed: %s", e)
        return None


def fallback_plan(task: str, request_id: str) -> dict:
    """Keyword-based fallback if LLM is unavailable. Returns a single-agent plan."""
    agent, team_id = route_task_to_agent(task)
    
    log_orchestration_event(
        request_id=request_id,
        event_type="fallback_routing",
        agent_id=agent["id"],
        orchestration_mode="single",
        message=f"Using fallback keyword routing to {agent['name']}"
    )
    
    return {
        "mode": "single",
        "rationale": "Routed via keyword match (LLM unavailable).",
        "steps": [{
            "agent_id": agent["id"],
            "agent_name": agent["name"],
            "team_id": team_id,
            "instruction": task,
        }],
    }


def now_iso() -> str:
    """Return current timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()