"""Simplified CEO Agent Flow

This module implements a simplified CEO agent architecture with the following flow:
1. Ask and clarify requirements from user
2. Create polished requirements in prompt format
3. Hit /orchestrate endpoint to get steps with agents
4. Delegate tasks to agents sequentially
5. Manage inter-agent communication
6. Know request payload format for each agent
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import httpx
from enum import Enum
from src.core.agent_state_manager import state_manager


class CEOFlowState(Enum):
    """States for the simplified CEO flow"""
    CLARIFYING_REQUIREMENTS = "clarifying_requirements"
    FORMATTING_REQUIREMENTS = "formatting_requirements"
    ORCHESTRATING = "orchestrating"
    DELEGATING = "delegating"
    PROCESSING_RESPONSE = "processing_response"
    COMPLETED = "completed"
    FAILED = "failed"


class SimplifiedCEOAgent:
    """Simplified CEO Agent with clear sequential flow"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "http://localhost:8000"
        self.current_state = CEOFlowState.CLARIFYING_REQUIREMENTS
        
        # Agent endpoint mappings - use underscore format to match actual routes
        self.agent_endpoints = {
            "content_writer": "/api/agents/content_writer",
            "social_publisher": "/api/agents/social_publisher",
            "social_media_publisher": "/api/agents/social_publisher",
            "code_architect": "/api/agents/code-architect",
            "ux_designer": "/api/agents/ux-designer",
            "qa_tester": "/api/agents/qa-tester",
            "business_analyst": "/api/agents/business-analyst",
            "project_manager": "/api/agents/project-manager",
            "data_analyst": "/api/agents/data-analyst",
            "devops_engineer": "/api/agents/devops-engineer",
            "seo_specialist": "/api/agents/seo-specialist",
            "ad_copywriter": "/api/agents/ad-copywriter",
            "analytics_agent": "/api/agents/analytics-agent",
            "frontend_engineer": "/api/agents/frontend-engineer",
            "backend_engineer": "/api/agents/backend-engineer",
            "devops_agent": "/api/agents/devops-agent",
            "qa_agent": "/api/agents/qa-agent",
            "architect_agent": "/api/agents/architect-agent",
            "lead_researcher": "/api/agents/lead-researcher",
            "outreach_agent": "/api/agents/outreach-agent",
            "demo_agent": "/api/agents/demo-agent",
            "negotiator_agent": "/api/agents/negotiator-agent",
            "crm_agent": "/api/agents/crm-agent",
            "user_researcher": "/api/agents/user-researcher",
            "pm_agent": "/api/agents/pm-agent",
            "designer_agent": "/api/agents/designer-agent",
            "roadmap_agent": "/api/agents/roadmap-agent",
            "feedback_agent": "/api/agents/feedback-agent"
        }
        
        # Agent request payload formats
        self.agent_payload_formats = {
            "content_writer": {
                "task": "string",
                "context": "optional<string>",
                "tone": "optional<string>",
                "format": "optional<string>"
            },
            "social_publisher": {
                "task": "string",
                "content": "optional<string>",
                "platform": "optional<string>",
                "caption": "optional<string>",
                "hashtags": "optional<list>",
                "media_url": "optional<string>"
            },
            "social_media_publisher": {
                "task": "string",
                "content": "optional<string>",
                "platform": "optional<string>",
                "caption": "optional<string>",
                "hashtags": "optional<list>",
                "media_url": "optional<string>"
            },
            "code_architect": {
                "task": "string",
                "requirements": "optional<dict>",
                "technology_stack": "optional<list>",
                "constraints": "optional<list>"
            },
            "ux_designer": {
                "task": "string",
                "user_personas": "optional<list>",
                "design_principles": "optional<list>",
                "wireframes_needed": "optional<bool>"
            },
            "qa_tester": {
                "task": "string",
                "test_types": "optional<list>",
                "acceptance_criteria": "optional<list>",
                "code_to_test": "optional<string>"
            },
            "business_analyst": {
                "task": "string",
                "business_context": "optional<string>",
                "stakeholders": "optional<list>",
                "success_metrics": "optional<list>"
            },
            "project_manager": {
                "task": "string",
                "timeline": "optional<string>",
                "resources": "optional<list>",
                "milestones": "optional<list>"
            },
            "data_analyst": {
                "task": "string",
                "data_sources": "optional<list>",
                "metrics": "optional<list>",
                "visualization_type": "optional<string>"
            },
            "devops_engineer": {
                "task": "string",
                "infrastructure": "optional<dict>",
                "deployment_target": "optional<string>",
                "ci_cd_requirements": "optional<list>"
            }
        }
    
    async def process_user_task(self, task: str, session_id: str) -> Dict[str, Any]:
        """Main entry point for processing user tasks"""
        try:
            self.logger.info(f"[CEO_SIMPLIFIED] Starting task processing for session {session_id}")
            
            # Step 1: Clarify requirements
            clarified_requirements = await self.clarify_requirements(task, session_id)
            
            # Step 2: Format requirements
            polished_requirements = self.format_requirements(clarified_requirements)
            
            # Step 3: Get orchestration plan
            orchestration_plan = await self.get_orchestration_plan(polished_requirements, session_id)
            
            # Step 4: Execute plan sequentially
            execution_results = await self.execute_plan_sequentially(orchestration_plan, polished_requirements, session_id)
            
            # Ensure state is set to COMPLETED after successful execution
            if self.current_state != CEOFlowState.FAILED:
                self.current_state = CEOFlowState.COMPLETED
            
            return {
                "success": True,
                "session_id": session_id,
                "original_task": task,
                "polished_requirements": polished_requirements,
                "orchestration_plan": orchestration_plan,
                "execution_results": execution_results,
                "final_state": self.current_state.value
            }
            
        except Exception as e:
            self.logger.error(f"[CEO_SIMPLIFIED] Error processing task: {e}")
            self.current_state = CEOFlowState.FAILED
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id,
                "final_state": self.current_state.value
            }
    
    async def clarify_requirements(self, task: str, session_id: str) -> Dict[str, Any]:
        """Step 1: Clarify requirements with user"""
        self.current_state = CEOFlowState.CLARIFYING_REQUIREMENTS
        self.logger.info(f"[CEO_SIMPLIFIED] Clarifying requirements for task: {task[:100]}...")
        
        # This would integrate with the existing conversation flow
        # For now, return a structured requirements dict
        return {
            "original_task": task,
            "purpose": "Extract from conversation",
            "target_audience": "Extract from conversation",
            "scope": "Extract from conversation",
            "constraints": "Extract from conversation",
            "timeline": "Extract from conversation",
            "success_criteria": ["Extract from conversation"]
        }
    
    def format_requirements(self, clarified_requirements: Dict[str, Any]) -> str:
        """Step 2: Format requirements into polished prompt"""
        self.current_state = CEOFlowState.FORMATTING_REQUIREMENTS
        self.logger.info("[CEO_SIMPLIFIED] Formatting requirements into polished prompt")
        
        # Create a well-structured prompt from requirements
        polished_prompt = f"""
Task: {clarified_requirements.get('original_task', 'Not specified')}

Purpose: {clarified_requirements.get('purpose', 'Not specified')}

Target Audience: {clarified_requirements.get('target_audience', 'Not specified')}

Scope: {clarified_requirements.get('scope', 'Not specified')}

Constraints: {clarified_requirements.get('constraints', 'None')}

Timeline: {clarified_requirements.get('timeline', 'Flexible')}

Success Criteria:
{chr(10).join(['- ' + criterion for criterion in clarified_requirements.get('success_criteria', ['Complete the task successfully'])])}
"""
        
        return polished_prompt.strip()
    
    async def get_orchestration_plan(self, polished_requirements: str, session_id: str) -> Dict[str, Any]:
        """Step 3: Get orchestration plan from /orchestrate endpoint"""
        self.current_state = CEOFlowState.ORCHESTRATING
        self.logger.info(f"[CEO_SIMPLIFIED] Getting orchestration plan for session {session_id}")
        
        # Validate polished_requirements is not None or empty
        if not polished_requirements:
            self.logger.error(f"[CEO_SIMPLIFIED] Polished requirements is None or empty for session {session_id}")
            raise ValueError("Polished requirements cannot be None or empty")
        
        try:
            # Log the task being sent to orchestration
            self.logger.info(f"[CEO_SIMPLIFIED] Sending task to orchestration: {polished_requirements[:200]}...")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/orchestrate",
                    json={"task": polished_requirements},
                    headers={"X-Request-ID": session_id}
                )
                
                if response.status_code == 200:
                    plan = response.json()
                    self.logger.info(f"[CEO_SIMPLIFIED] Orchestration plan received: {plan.get('mode')} mode with {len(plan.get('steps', []))} steps")
                    return plan
                else:
                    raise Exception(f"Orchestration failed with status {response.status_code}: {response.text}")
                    
        except Exception as e:
            self.logger.error(f"[CEO_SIMPLIFIED] Orchestration error: {e}")
            raise
    
    async def execute_plan_sequentially(self, orchestration_plan: Dict[str, Any], polished_requirements: str, session_id: str) -> List[Dict[str, Any]]:
        """Step 4 & 5: Execute plan sequentially and manage inter-agent communication"""
        self.current_state = CEOFlowState.DELEGATING
        self.logger.info(f"[CEO_SIMPLIFIED] Starting sequential execution of {len(orchestration_plan.get('steps', []))} agents")
        self.logger.debug(f"[CEO_DEBUG] Session ID: {session_id}")
        self.logger.debug(f"[CEO_DEBUG] Orchestration plan: {json.dumps(orchestration_plan, indent=2)}")
        
        # Save orchestration context to state manager
        state_manager.save_orchestration_context(session_id, {
            "orchestration_plan": orchestration_plan,
            "polished_requirements": polished_requirements,
            "start_time": datetime.now(timezone.utc).isoformat()
        })
        
        execution_results = []
        previous_output = None
        
        for idx, step in enumerate(orchestration_plan.get('steps', [])):
            agent_id = step.get('agent_id')
            agent_name = step.get('agent_name')
            instruction = step.get('instruction')
            endpoint = step.get('endpoint')
            
            self.logger.info(f"[CEO_SIMPLIFIED] Executing step {idx + 1}: {agent_name}")
            self.logger.debug(f"[CEO_DEBUG] Agent ID: {agent_id}, Endpoint: {endpoint}")
            
            # Get previous agent output from state manager if available
            if idx > 0 and execution_results:
                previous_agent_id = execution_results[-1].get('agent_id')
                self.logger.debug(f"[CEO_DEBUG] Attempting to retrieve output from previous agent: {previous_agent_id}")
                previous_output = state_manager.get_agent_output(session_id, previous_agent_id)
                if previous_output:
                    output_preview = str(previous_output)[:200] + "..." if len(str(previous_output)) > 200 else str(previous_output)
                    self.logger.info(f"[CEO_SIMPLIFIED] Retrieved previous output from state manager for {previous_agent_id}")
                    self.logger.debug(f"[CEO_DEBUG] Previous output preview: {output_preview}")
                else:
                    self.logger.warning(f"[CEO_DEBUG] No previous output found for {previous_agent_id}")
            
            # Prepare request payload based on agent type
            request_payload = self.prepare_agent_request(
                agent_id=agent_id,
                instruction=instruction,
                previous_output=previous_output,
                context={
                    "polished_requirements": polished_requirements,
                    "step_number": idx + 1,
                    "total_steps": len(orchestration_plan.get('steps', [])),
                    "previous_agent": execution_results[-1].get('agent_name') if execution_results else None
                }
            )
            
            self.logger.debug(f"[CEO_DEBUG] Request payload for {agent_name}: {json.dumps(request_payload, indent=2)}")
            
            # Execute agent with session ID in headers for state management
            agent_result = await self.execute_agent(
                agent_id=agent_id,
                agent_name=agent_name,
                endpoint=endpoint,
                payload=request_payload,
                session_id=session_id
            )
            
            self.logger.debug(f"[CEO_DEBUG] Agent result: {json.dumps(agent_result, indent=2) if isinstance(agent_result, dict) else str(agent_result)}")
            
            # Process response
            self.current_state = CEOFlowState.PROCESSING_RESPONSE
            processed_result = self.process_agent_response(agent_result)
            execution_results.append(processed_result)
            
            # Save agent output to state manager
            if processed_result.get('success'):
                output = processed_result.get('output', '')
                output_preview = str(output)[:200] + "..." if len(str(output)) > 200 else str(output)
                self.logger.debug(f"[CEO_DEBUG] Saving output to state manager - Agent: {agent_id}, Output preview: {output_preview}")
                
                state_manager.save_agent_output(
                    session_id=session_id,
                    agent_id=agent_id,
                    output=output,
                    metadata={
                        "agent_name": agent_name,
                        "step_number": idx + 1,
                        "instruction": instruction,
                        "duration_ms": processed_result.get('duration_ms', 0)
                    }
                )
                self.logger.info(f"[CEO_SIMPLIFIED] Saved {agent_name} output to state manager")
                previous_output = output
            else:
                self.logger.warning(f"[CEO_SIMPLIFIED] Agent {agent_name} failed, continuing with empty output")
                self.logger.debug(f"[CEO_DEBUG] Failed result: {processed_result}")
                previous_output = None
            
            self.current_state = CEOFlowState.DELEGATING
        
        self.current_state = CEOFlowState.COMPLETED
        self.logger.info(f"[CEO_SIMPLIFIED] Execution completed with {len(execution_results)} results")
        self.logger.debug(f"[CEO_DEBUG] Final execution results: {json.dumps(execution_results, indent=2) if execution_results else 'No results'}")
        return execution_results
    
    def prepare_agent_request(self, agent_id: str, instruction: str, previous_output: Optional[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Step 6: Prepare request payload for specific agent"""
        self.logger.info(f"[CEO_SIMPLIFIED] Preparing request for agent {agent_id}")
        self.logger.debug(f"[CEO_DEBUG] Instruction: {instruction}")
        self.logger.debug(f"[CEO_DEBUG] Has previous output: {bool(previous_output)}")
        self.logger.debug(f"[CEO_DEBUG] Context: {context}")
        
        # Base payload
        payload = {
            "task": instruction
        }
        
        # Add previous agent output if available and relevant
        if previous_output and context.get('previous_agent'):
            payload["context"] = f"Previous work from {context['previous_agent']}:\n{previous_output}"
            self.logger.debug(f"[CEO_DEBUG] Added context from previous agent: {context['previous_agent']}")
        
        # Add agent-specific fields based on agent type
        if agent_id == "content_writer":
            payload["format"] = "structured"
            payload["tone"] = "professional"
            self.logger.debug(f"[CEO_DEBUG] Content Writer payload configured")
        elif agent_id in ["social_publisher", "social_media_publisher"]:
            # For social media publisher, pass content from previous agent (content writer)
            if previous_output:
                # Extract the actual content from Content Writer's output
                # Previous output should contain the generated caption and hashtags
                output_preview = str(previous_output)[:500] + "..." if len(str(previous_output)) > 500 else str(previous_output)
                self.logger.info(f"[CEO_SIMPLIFIED] Passing content to social publisher")
                self.logger.debug(f"[CEO_DEBUG] Previous output for social publisher: {output_preview}")
                
                # CRITICAL FIX: Use the actual content from Content Writer, not the instruction
                payload["content"] = previous_output
                payload["caption"] = previous_output  # Use content as caption for Instagram
                
                # Log what we're actually sending
                self.logger.info(f"[CEO_DEBUG] Social publisher payload content: {payload['content'][:200]}...")
                self.logger.info(f"[CEO_DEBUG] Social publisher payload caption: {payload['caption'][:200]}...")
            else:
                # If no previous output, use the instruction as fallback
                self.logger.warning(f"[CEO_SIMPLIFIED] No previous output for social publisher, using instruction: {instruction}")
                payload["content"] = instruction
                payload["caption"] = instruction
            payload["platform"] = "instagram"  # Default to Instagram
            payload["hashtags"] = []  # Can be extracted from content or added later
            
            self.logger.debug(f"[CEO_DEBUG] Final social publisher payload: {json.dumps(payload, indent=2)}")
        elif agent_id == "code_architect":
            payload["requirements"] = {
                "from_previous_agent": bool(previous_output),
                "original_requirements": context.get('polished_requirements')
            }
        elif agent_id == "qa_tester" and previous_output:
            payload["code_to_test"] = previous_output
            payload["test_types"] = ["unit", "integration"]
        elif agent_id == "ux_designer":
            payload["wireframes_needed"] = True
        elif agent_id == "business_analyst":
            payload["business_context"] = context.get('polished_requirements')
        elif agent_id == "project_manager":
            payload["timeline"] = "Based on requirements"
        elif agent_id == "data_analyst":
            payload["visualization_type"] = "dashboard"
        elif agent_id == "devops_engineer":
            payload["deployment_target"] = "production"
        
        return payload
    
    async def execute_agent(self, agent_id: str, agent_name: str, endpoint: str, payload: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Execute a single agent with the prepared payload"""
        self.logger.info(f"[CEO_SIMPLIFIED] Executing agent {agent_name} at {endpoint}")
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}{endpoint}",
                    json=payload,
                    headers={
                        "X-Request-ID": session_id,
                        "X-Session-ID": session_id,  # Add session ID for state management
                        "X-Agent-Chain": agent_id
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.logger.info(f"[CEO_SIMPLIFIED] Agent {agent_name} executed successfully")
                    return {
                        "success": True,
                        "agent_id": agent_id,
                        "agent_name": agent_name,
                        "response": result
                    }
                else:
                    self.logger.error(f"[CEO_SIMPLIFIED] Agent {agent_name} failed with status {response.status_code}")
                    return {
                        "success": False,
                        "agent_id": agent_id,
                        "agent_name": agent_name,
                        "error": f"Status {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            self.logger.error(f"[CEO_SIMPLIFIED] Error executing agent {agent_name}: {e}")
            return {
                "success": False,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "error": str(e)
            }
    
    def process_agent_response(self, agent_result: Dict[str, Any]) -> Dict[str, Any]:
        """Process and extract relevant information from agent response"""
        if not agent_result.get('success'):
            return agent_result
        
        response = agent_result.get('response', {})
        
        # Extract output based on response structure
        output = ""
        if isinstance(response, dict):
            # Check multiple possible fields where content might be stored
            output = response.get('output', response.get('result', response.get('content', 
                    response.get('generated_content', response.get('text', str(response))))))
        else:
            output = str(response)
        
        # Log the extracted output for debugging
        self.logger.info(f"[CEO_SIMPLIFIED] Extracted output from agent response: {output[:200]}...")
        
        return {
            "agent_id": agent_result.get('agent_id'),
            "agent_name": agent_result.get('agent_name'),
            "success": True,
            "output": output,
            "duration_ms": response.get('duration_ms', 0),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_agent_payload_format(self, agent_id: str) -> Dict[str, Any]:
        """Get the expected payload format for a specific agent"""
        return self.agent_payload_formats.get(agent_id, {
            "task": "string",
            "context": "optional<string>"
        })


# Global instance
simplified_ceo_agent = SimplifiedCEOAgent()
