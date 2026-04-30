from typing import Dict, List, Any, Optional, Tuple
import json
import logging
import uuid
from datetime import datetime, timezone
from ai_service import ai_service
from ceo_learning_system import ceo_learning_system


class CEOAgentPlanner:
    """Agent selection and planning system for CEO agent"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.learning_system = ceo_learning_system
        
        # Define available agents and their capabilities
        self.available_agents = {
            "content_writer": {
                "name": "Content Writer Agent",
                "capabilities": ["blog", "article", "content", "copy", "writing", "documentation"],
                "endpoint": "/api/agents/content-writer",
                "team": "content"
            },
            "social_media_publisher": {
                "name": "Social Media Publisher Agent",
                "capabilities": ["social", "post", "instagram", "twitter", "linkedin", "facebook"],
                "endpoint": "/api/agents/social-media",
                "team": "marketing"
            },
            "unit_test": {
                "name": "Unit Test Agent",
                "capabilities": ["test", "testing", "unit test", "coverage", "quality"],
                "endpoint": "/api/agents/unit-test",
                "team": "engineering"
            },
            "pr_agent": {
                "name": "PR Agent",
                "capabilities": ["pull request", "code review", "pr", "merge", "review"],
                "endpoint": "/api/agents/pr",
                "team": "engineering"
            },
            "sonar_agent": {
                "name": "Sonar Agent",
                "capabilities": ["code quality", "sonar", "static analysis", "security scan", "vulnerability"],
                "endpoint": "/api/agents/sonar",
                "team": "engineering"
            }
        }
        
        # Define workflow patterns
        self.workflow_patterns = {
            "content_creation": ["content_writer", "social_media_publisher"],
            "code_development": ["unit_test", "sonar_agent", "pr_agent"],
            "marketing_campaign": ["content_writer", "social_media_publisher"],
            "quality_assurance": ["unit_test", "sonar_agent"]
        }
    
    async def create_agent_plan(self, 
                              requirements: Dict[str, Any], 
                              request_id: str) -> Dict[str, Any]:
        """Create an agent execution plan based on requirements"""
        
        try:
            # Extract key information from requirements
            task_description = requirements.get("polished_task", "")
            objective = requirements.get("objective", "")
            deliverables = requirements.get("deliverables", [])
            
            # Analyze task to determine agent needs
            agent_analysis = await self._analyze_agent_requirements(
                task_description, objective, deliverables, request_id
            )
            
            # Select appropriate agents
            selected_agents = self._select_agents(agent_analysis)
            
            # Determine workflow pattern
            workflow = self._determine_workflow(selected_agents, agent_analysis)
            
            # Create execution plan
            execution_plan = self._create_execution_plan(
                selected_agents, workflow, requirements
            )
            
            # Apply learning insights
            enhanced_plan = self._apply_learning_insights(execution_plan)
            
            return {
                "success": True,
                "plan": enhanced_plan,
                "agent_analysis": agent_analysis,
                "selected_agents": selected_agents,
                "workflow": workflow,
                "estimated_duration": self._estimate_duration(enhanced_plan),
                "confidence_score": self._calculate_confidence(agent_analysis, selected_agents)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create agent plan: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_plan": self._create_fallback_plan(requirements)
            }
    
    async def _analyze_agent_requirements(self, 
                                        task: str, 
                                        objective: str, 
                                        deliverables: List[str],
                                        request_id: str) -> Dict[str, Any]:
        """Analyze requirements to determine which agents are needed"""
        
        prompt = f"""
Analyze this task and determine which types of agents/specialists would be needed:

Task: {task}
Objective: {objective}
Deliverables: {', '.join(deliverables)}

Available agent types:
- Content Writer: Creates blogs, articles, documentation
- Social Media Publisher: Manages social media posts and campaigns
- Unit Test Agent: Creates and runs unit tests
- PR Agent: Manages pull requests and code reviews
- Sonar Agent: Performs code quality and security analysis

Return a JSON object with:
{{
    "primary_domain": "content/engineering/marketing",
    "required_agents": ["list of agent types needed"],
    "agent_rationale": {{
        "agent_type": "reason why this agent is needed"
    }},
    "workflow_type": "sequential/parallel/mixed",
    "dependencies": ["agent dependencies if any"]
}}
"""
        
        try:
            result = await ai_service.generate_content(prompt, request_id)
            analysis = json.loads(result)
            
            # Validate and enhance analysis
            return self._validate_agent_analysis(analysis)
            
        except Exception as e:
            self.logger.error(f"Agent analysis failed: {e}")
            # Fallback analysis based on keywords
            return self._keyword_based_analysis(task, objective, deliverables)
    
    def _validate_agent_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance agent analysis"""
        
        # Ensure required fields
        validated = {
            "primary_domain": analysis.get("primary_domain", "general"),
            "required_agents": analysis.get("required_agents", []),
            "agent_rationale": analysis.get("agent_rationale", {}),
            "workflow_type": analysis.get("workflow_type", "sequential"),
            "dependencies": analysis.get("dependencies", [])
        }
        
        # Validate agent names
        valid_agents = []
        for agent in validated["required_agents"]:
            agent_key = self._normalize_agent_name(agent)
            if agent_key in self.available_agents:
                valid_agents.append(agent_key)
        
        validated["required_agents"] = valid_agents
        
        return validated
    
    def _keyword_based_analysis(self, task: str, objective: str, deliverables: List[str]) -> Dict[str, Any]:
        """Fallback keyword-based analysis"""
        
        combined_text = f"{task} {objective} {' '.join(deliverables)}".lower()
        required_agents = []
        agent_rationale = {}
        
        # Check for content creation needs
        if any(keyword in combined_text for keyword in ["blog", "article", "content", "write", "copy"]):
            required_agents.append("content_writer")
            agent_rationale["content_writer"] = "Content creation detected in requirements"
        
        # Check for social media needs
        if any(keyword in combined_text for keyword in ["social", "post", "instagram", "twitter"]):
            required_agents.append("social_media_publisher")
            agent_rationale["social_media_publisher"] = "Social media publishing detected"
        
        # Check for testing needs
        if any(keyword in combined_text for keyword in ["test", "quality", "coverage"]):
            required_agents.append("unit_test")
            agent_rationale["unit_test"] = "Testing requirements detected"
        
        # Check for code review needs
        if any(keyword in combined_text for keyword in ["review", "pr", "pull request"]):
            required_agents.append("pr_agent")
            agent_rationale["pr_agent"] = "Code review requirements detected"
        
        # Determine primary domain
        if "content_writer" in required_agents or "social_media_publisher" in required_agents:
            primary_domain = "content"
        elif any(agent in required_agents for agent in ["unit_test", "pr_agent", "sonar_agent"]):
            primary_domain = "engineering"
        else:
            primary_domain = "general"
        
        return {
            "primary_domain": primary_domain,
            "required_agents": required_agents if required_agents else ["content_writer"],
            "agent_rationale": agent_rationale,
            "workflow_type": "sequential",
            "dependencies": []
        }
    
    def _normalize_agent_name(self, agent_name: str) -> str:
        """Normalize agent name to match available agents"""
        
        agent_lower = agent_name.lower().replace(" ", "_")
        
        # Direct match
        if agent_lower in self.available_agents:
            return agent_lower
        
        # Partial match
        for key in self.available_agents:
            if key in agent_lower or agent_lower in key:
                return key
        
        # Keyword match
        keyword_map = {
            "content": "content_writer",
            "social": "social_media_publisher",
            "test": "unit_test",
            "pr": "pr_agent",
            "sonar": "sonar_agent",
            "quality": "sonar_agent"
        }
        
        for keyword, agent_key in keyword_map.items():
            if keyword in agent_lower:
                return agent_key
        
        return agent_name  # Return original if no match
    
    def _select_agents(self, agent_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Select specific agents based on analysis"""
        
        selected = []
        
        for agent_key in agent_analysis["required_agents"]:
            if agent_key in self.available_agents:
                agent_info = self.available_agents[agent_key].copy()
                agent_info["id"] = agent_key
                agent_info["rationale"] = agent_analysis["agent_rationale"].get(
                    agent_key, "Selected based on task requirements"
                )
                selected.append(agent_info)
        
        return selected
    
    def _determine_workflow(self, selected_agents: List[Dict], agent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Determine the workflow pattern for selected agents"""
        
        workflow_type = agent_analysis.get("workflow_type", "sequential")
        agent_ids = [agent["id"] for agent in selected_agents]
        
        # Check for known patterns
        for pattern_name, pattern_agents in self.workflow_patterns.items():
            if all(agent in agent_ids for agent in pattern_agents[:len(agent_ids)]):
                return {
                    "type": workflow_type,
                    "pattern": pattern_name,
                    "sequence": pattern_agents[:len(agent_ids)],
                    "parallel_groups": self._identify_parallel_groups(agent_ids, agent_analysis)
                }
        
        # Default workflow
        return {
            "type": workflow_type,
            "pattern": "custom",
            "sequence": agent_ids,
            "parallel_groups": self._identify_parallel_groups(agent_ids, agent_analysis)
        }
    
    def _identify_parallel_groups(self, agent_ids: List[str], agent_analysis: Dict[str, Any]) -> List[List[str]]:
        """Identify which agents can run in parallel"""
        
        # Agents that can typically run in parallel
        parallel_compatible = {
            "unit_test": ["sonar_agent"],
            "sonar_agent": ["unit_test"],
            "content_writer": ["social_media_publisher"]
        }
        
        parallel_groups = []
        processed = set()
        
        for agent_id in agent_ids:
            if agent_id not in processed:
                group = [agent_id]
                processed.add(agent_id)
                
                # Check for compatible agents
                if agent_id in parallel_compatible:
                    for compatible in parallel_compatible[agent_id]:
                        if compatible in agent_ids and compatible not in processed:
                            group.append(compatible)
                            processed.add(compatible)
                
                parallel_groups.append(group)
        
        return parallel_groups
    
    def _create_execution_plan(self, 
                             selected_agents: List[Dict], 
                             workflow: Dict[str, Any],
                             requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed execution plan"""
        
        steps = []
        
        # Create steps based on workflow
        if workflow["type"] == "parallel" and workflow.get("parallel_groups"):
            # Parallel execution
            for i, group in enumerate(workflow["parallel_groups"]):
                parallel_steps = []
                for agent_id in group:
                    agent = next((a for a in selected_agents if a["id"] == agent_id), None)
                    if agent:
                        parallel_steps.append(self._create_step(agent, requirements, len(steps) + 1))
                
                steps.append({
                    "step_number": len(steps) + 1,
                    "type": "parallel",
                    "agents": parallel_steps
                })
        else:
            # Sequential execution
            for i, agent in enumerate(selected_agents):
                steps.append(self._create_step(agent, requirements, i + 1))
        
        return {
            "plan_id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "workflow_type": workflow["type"],
            "workflow_pattern": workflow["pattern"],
            "total_steps": len(steps),
            "steps": steps,
            "requirements_summary": {
                "objective": requirements.get("objective"),
                "deliverables": requirements.get("deliverables", []),
                "constraints": requirements.get("constraints", []),
                "timeline": requirements.get("timeline")
            }
        }
    
    def _create_step(self, agent: Dict[str, Any], requirements: Dict[str, Any], step_number: int) -> Dict[str, Any]:
        """Create individual step in execution plan"""
        
        # Generate specific instructions for the agent
        instructions = self._generate_agent_instructions(agent, requirements)
        
        return {
            "step_number": step_number,
            "agent_id": agent["id"],
            "agent_name": agent["name"],
            "team": agent["team"],
            "endpoint": agent["endpoint"],
            "instructions": instructions,
            "expected_output": self._define_expected_output(agent["id"], requirements),
            "success_criteria": self._define_success_criteria(agent["id"], requirements),
            "timeout_ms": self._determine_timeout(agent["id"]),
            "retry_policy": {
                "max_retries": 3,
                "backoff_ms": 1000
            }
        }
    
    def _generate_agent_instructions(self, agent: Dict[str, Any], requirements: Dict[str, Any]) -> str:
        """Generate specific instructions for an agent"""
        
        base_task = requirements.get("polished_task", "")
        objective = requirements.get("objective", "")
        
        # Agent-specific instruction templates
        instruction_templates = {
            "content_writer": f"Create content based on the following requirements:\n{base_task}\n\nObjective: {objective}\n\nEnsure the content aligns with the target audience and specified tone.",
            "social_media_publisher": f"Create and publish social media content based on:\n{base_task}\n\nTarget platforms and audience as specified in requirements.",
            "unit_test": f"Create comprehensive unit tests for:\n{base_task}\n\nEnsure high code coverage and test edge cases.",
            "pr_agent": f"Create a pull request with proper documentation for:\n{base_task}\n\nInclude clear description and review guidelines.",
            "sonar_agent": f"Perform code quality and security analysis for:\n{base_task}\n\nReport any critical issues or vulnerabilities."
        }
        
        return instruction_templates.get(
            agent["id"],
            f"Execute the following task:\n{base_task}\n\nObjective: {objective}"
        )
    
    def _define_expected_output(self, agent_id: str, requirements: Dict[str, Any]) -> str:
        """Define expected output for an agent"""
        
        output_definitions = {
            "content_writer": "Well-written content that meets all specified requirements",
            "social_media_publisher": "Published social media posts with engagement metrics",
            "unit_test": "Test suite with coverage report and all tests passing",
            "pr_agent": "Created pull request with proper documentation and review status",
            "sonar_agent": "Code quality report with identified issues and recommendations"
        }
        
        return output_definitions.get(agent_id, "Completed task output")
    
    def _define_success_criteria(self, agent_id: str, requirements: Dict[str, Any]) -> List[str]:
        """Define success criteria for an agent"""
        
        criteria_map = {
            "content_writer": [
                "Content meets word count requirements",
                "Appropriate tone and style maintained",
                "All key points addressed"
            ],
            "social_media_publisher": [
                "Posts published successfully",
                "Correct formatting for each platform",
                "Hashtags and mentions included"
            ],
            "unit_test": [
                "All tests pass",
                "Code coverage >= 80%",
                "Edge cases covered"
            ],
            "pr_agent": [
                "PR created successfully",
                "Proper documentation included",
                "No merge conflicts"
            ],
            "sonar_agent": [
                "Analysis completed without errors",
                "No critical vulnerabilities found",
                "Code quality metrics meet standards"
            ]
        }
        
        return criteria_map.get(agent_id, ["Task completed successfully"])
    
    def _determine_timeout(self, agent_id: str) -> int:
        """Determine appropriate timeout for agent"""
        
        # Timeout in milliseconds
        timeout_map = {
            "content_writer": 300000,      # 5 minutes
            "social_media_publisher": 120000,  # 2 minutes
            "unit_test": 600000,           # 10 minutes
            "pr_agent": 180000,            # 3 minutes
            "sonar_agent": 300000          # 5 minutes
        }
        
        return timeout_map.get(agent_id, 180000)  # Default 3 minutes
    
    def _apply_learning_insights(self, execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Apply learning system insights to enhance the plan"""
        
        enhanced_plan = execution_plan.copy()
        
        # Get learning insights
        learning_stats = self.learning_system.get_learning_stats()
        
        # Apply learned optimizations
        if learning_stats.get("total_delegations", 0) > 0:
            # Add learning metadata
            enhanced_plan["learning_applied"] = True
            enhanced_plan["learning_insights"] = {
                "patterns_detected": learning_stats.get("unique_patterns", 0),
                "optimizations_applied": []
            }
            
            # Check for output passing rules
            for i, step in enumerate(enhanced_plan["steps"]):
                if isinstance(step, dict) and "agent_id" in step:
                    agent_id = step["agent_id"]
                    
                    # Check if this agent typically passes output to next
                    if i + 1 < len(enhanced_plan["steps"]):
                        next_step = enhanced_plan["steps"][i + 1]
                        if isinstance(next_step, dict) and "agent_id" in next_step:
                            next_agent_id = next_step["agent_id"]
                            
                            if self.learning_system.should_pass_output(agent_id, next_agent_id):
                                step["pass_output_to_next"] = True
                                enhanced_plan["learning_insights"]["optimizations_applied"].append(
                                    f"Output passing: {agent_id} -> {next_agent_id}"
                                )
        
        return enhanced_plan
    
    def _estimate_duration(self, plan: Dict[str, Any]) -> int:
        """Estimate total duration for plan execution"""
        
        total_ms = 0
        
        for step in plan["steps"]:
            if isinstance(step, dict):
                if step.get("type") == "parallel":
                    # For parallel steps, take the maximum timeout
                    max_timeout = max(
                        agent.get("timeout_ms", 180000) 
                        for agent in step.get("agents", [])
                    )
                    total_ms += max_timeout
                else:
                    # For sequential steps
                    total_ms += step.get("timeout_ms", 180000)
        
        # Add buffer for overhead
        total_ms = int(total_ms * 1.2)
        
        return total_ms
    
    def _calculate_confidence(self, agent_analysis: Dict[str, Any], selected_agents: List[Dict]) -> float:
        """Calculate confidence score for the plan"""
        
        confidence = 0.5  # Base confidence
        
        # Increase confidence if all required agents were found
        if len(selected_agents) == len(agent_analysis.get("required_agents", [])):
            confidence += 0.2
        
        # Increase confidence for known workflow patterns
        if agent_analysis.get("workflow_pattern") != "custom":
            confidence += 0.15
        
        # Increase confidence if rationale is provided for all agents
        if all(agent.get("rationale") for agent in selected_agents):
            confidence += 0.15
        
        return min(confidence, 1.0)
    
    def _create_fallback_plan(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create a simple fallback plan"""
        
        return {
            "plan_id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "workflow_type": "sequential",
            "workflow_pattern": "fallback",
            "total_steps": 1,
            "steps": [
                {
                    "step_number": 1,
                    "agent_id": "content_writer",
                    "agent_name": "Content Writer Agent",
                    "team": "content",
                    "endpoint": "/api/agents/content-writer",
                    "instructions": f"Complete the following task: {requirements.get('polished_task', 'Task not specified')}",
                    "expected_output": "Completed task output",
                    "success_criteria": ["Task completed"],
                    "timeout_ms": 300000,
                    "retry_policy": {
                        "max_retries": 3,
                        "backoff_ms": 1000
                    }
                }
            ],
            "requirements_summary": {
                "objective": requirements.get("objective", "Complete the task"),
                "deliverables": requirements.get("deliverables", ["Task output"]),
                "constraints": requirements.get("constraints", []),
                "timeline": requirements.get("timeline", "As soon as possible")
            },
            "is_fallback": True
        }
    
    def validate_plan(self, plan: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate the execution plan"""
        
        issues = []
        
        # Check for required fields
        required_fields = ["plan_id", "steps", "workflow_type"]
        for field in required_fields:
            if field not in plan:
                issues.append(f"Missing required field: {field}")
        
        # Validate steps
        if "steps" in plan:
            if not plan["steps"]:
                issues.append("Plan has no steps")
            else:
                for i, step in enumerate(plan["steps"]):
                    step_issues = self._validate_step(step, i)
                    issues.extend(step_issues)
        
        # Check agent availability
        if "steps" in plan:
            for step in plan["steps"]:
                if isinstance(step, dict) and "agent_id" in step:
                    if step["agent_id"] not in self.available_agents:
                        issues.append(f"Unknown agent: {step['agent_id']}")
        
        return len(issues) == 0, issues
    
    def _validate_step(self, step: Dict[str, Any], index: int) -> List[str]:
        """Validate individual step"""
        
        issues = []
        
        if step.get("type") == "parallel":
            # Validate parallel step
            if "agents" not in step or not step["agents"]:
                issues.append(f"Step {index + 1}: Parallel step has no agents")
        else:
            # Validate sequential step
            required = ["agent_id", "instructions", "endpoint"]
            for field in required:
                if field not in step:
                    issues.append(f"Step {index + 1}: Missing required field '{field}'")
        
        return issues


# Create global instance
ceo_agent_planner = CEOAgentPlanner()
