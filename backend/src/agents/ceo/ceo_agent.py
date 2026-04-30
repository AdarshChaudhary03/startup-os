import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from .ceo_learning_system import ceo_learning_system

class CEOAgent:
    """
    CEO Agent with learning capabilities for intelligent delegation
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.learning_system = ceo_learning_system
        
    def analyze_agent_response(self, agent_response: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze agent response and extract relevant information"""
        try:
            analysis = {
                "agent_id": agent_response.get("agent_id"),
                "agent_name": agent_response.get("agent_name"),
                "task_completed": agent_response.get("success", False),
                "output_content": agent_response.get("output", ""),
                "error": agent_response.get("error"),
                "duration": agent_response.get("duration_ms", 0),
                "timestamp": agent_response.get("timestamp"),
                "has_output": bool(agent_response.get("output", "").strip())
            }
            
            self.logger.info(f"Analyzed response from {analysis['agent_name']}: Success={analysis['task_completed']}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing agent response: {e}")
            return {
                "agent_id": "unknown",
                "agent_name": "Unknown",
                "task_completed": False,
                "output_content": "",
                "error": str(e),
                "has_output": False
            }
    
    def determine_next_agent(self, 
                           current_agent: str, 
                           workflow_sequence: List[str], 
                           agent_analysis: Dict[str, Any]) -> Optional[str]:
        """Determine the next agent in the workflow sequence"""
        try:
            if current_agent not in workflow_sequence:
                self.logger.warning(f"Current agent {current_agent} not found in workflow sequence")
                return None
            
            current_index = workflow_sequence.index(current_agent)
            
            # Check if there's a next agent
            if current_index + 1 < len(workflow_sequence):
                next_agent = workflow_sequence[current_index + 1]
                self.logger.info(f"Next agent determined: {next_agent}")
                return next_agent
            else:
                self.logger.info("Workflow completed - no next agent")
                return None
                
        except Exception as e:
            self.logger.error(f"Error determining next agent: {e}")
            return None
    
    def prepare_delegation_task(self, 
                              source_agent: str,
                              target_agent: str, 
                              original_task: str,
                              source_agent_response: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare task for delegation using learning system"""
        try:
            # Check if we should pass output from source to target agent
            should_pass = self.learning_system.should_pass_output(source_agent, target_agent)
            
            if should_pass:
                # Extract output from source agent
                output_field = self.learning_system.get_output_field(source_agent, target_agent)
                source_output = self.learning_system.extract_agent_output(source_agent_response, output_field)
                
                if source_output:
                    # Format task with source output
                    formatted_task = self.learning_system.format_task_with_output(
                        original_task, source_output, target_agent
                    )
                    
                    delegation_info = {
                        "task": formatted_task,
                        "source_agent": source_agent,
                        "target_agent": target_agent,
                        "used_learning_rule": True,
                        "source_output_included": True,
                        "learning_applied": f"Passed output from {source_agent} to {target_agent}",
                        "original_task": original_task,
                        "source_output_preview": source_output[:200] + "..." if len(source_output) > 200 else source_output
                    }
                    
                    self.logger.info(f"Applied learning rule: {source_agent} -> {target_agent}")
                    return delegation_info
            
            # Default delegation without output passing
            delegation_info = {
                "task": original_task,
                "source_agent": source_agent,
                "target_agent": target_agent,
                "used_learning_rule": False,
                "source_output_included": False,
                "learning_applied": "No specific learning rule applied",
                "original_task": original_task
            }
            
            return delegation_info
            
        except Exception as e:
            self.logger.error(f"Error preparing delegation task: {e}")
            return {
                "task": original_task,
                "source_agent": source_agent,
                "target_agent": target_agent,
                "used_learning_rule": False,
                "source_output_included": False,
                "learning_applied": f"Error: {str(e)}",
                "original_task": original_task
            }
    
    def process_agent_completion(self, 
                               agent_response: Dict[str, Any],
                               workflow_sequence: List[str],
                               original_task: str) -> Dict[str, Any]:
        """Process agent completion and prepare for next delegation"""
        try:
            # Analyze the agent response
            analysis = self.analyze_agent_response(agent_response)
            
            if not analysis["task_completed"]:
                return {
                    "status": "error",
                    "message": f"Agent {analysis['agent_name']} failed to complete task",
                    "error": analysis.get("error"),
                    "next_action": "retry_or_abort"
                }
            
            # Determine next agent
            current_agent = analysis["agent_id"]
            next_agent = self.determine_next_agent(current_agent, workflow_sequence, analysis)
            
            if not next_agent:
                return {
                    "status": "completed",
                    "message": "Workflow completed successfully",
                    "final_output": analysis["output_content"],
                    "next_action": "workflow_complete"
                }
            
            # Prepare delegation for next agent
            delegation_info = self.prepare_delegation_task(
                source_agent=current_agent,
                target_agent=next_agent,
                original_task=original_task,
                source_agent_response=agent_response
            )
            
            return {
                "status": "continue",
                "message": f"Delegating from {analysis['agent_name']} to {next_agent}",
                "next_agent": next_agent,
                "delegation_info": delegation_info,
                "source_analysis": analysis,
                "next_action": "delegate_to_next_agent"
            }
            
        except Exception as e:
            self.logger.error(f"Error processing agent completion: {e}")
            return {
                "status": "error",
                "message": f"Error processing agent completion: {str(e)}",
                "next_action": "handle_error"
            }
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights about current learning patterns"""
        try:
            stats = self.learning_system.get_learning_stats()
            all_learnings = self.learning_system.get_all_learnings()
            
            return {
                "statistics": stats,
                "active_rules": len(all_learnings.get("output_passing_rules", {})),
                "delegation_patterns": all_learnings.get("delegation_patterns", []),
                "recent_learnings": all_learnings.get("delegation_patterns", [])[-5:],  # Last 5 learnings
                "learning_status": "active"
            }
        except Exception as e:
            self.logger.error(f"Error getting learning insights: {e}")
            return {
                "statistics": {},
                "active_rules": 0,
                "learning_status": "error",
                "error": str(e)
            }


# Global CEO agent instance
ceo_agent = CEOAgent()
