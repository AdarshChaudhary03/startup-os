import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

class CEOLearningSystem:
    """
    RAG-based learning system for CEO agent to store and retrieve delegation patterns
    """
    
    def __init__(self, learning_file_path: str = "ceo_learning_memory.json"):
        self.learning_file_path = learning_file_path
        self.logger = logging.getLogger(__name__)
        self.learning_memory = self._load_learning_memory()
        
    def _load_learning_memory(self) -> Dict[str, Any]:
        """Load existing learning memory from file"""
        try:
            if os.path.exists(self.learning_file_path):
                with open(self.learning_file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {
                    "delegation_patterns": [],
                    "agent_sequences": {},
                    "output_passing_rules": {},
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"Error loading learning memory: {e}")
            return {
                "delegation_patterns": [],
                "agent_sequences": {},
                "output_passing_rules": {},
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
    
    def _save_learning_memory(self):
        """Save learning memory to file"""
        try:
            self.learning_memory["last_updated"] = datetime.now().isoformat()
            with open(self.learning_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.learning_memory, f, indent=2, ensure_ascii=False)
            self.logger.info("Learning memory saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving learning memory: {e}")
    
    def add_delegation_learning(self, 
                              source_agent: str, 
                              target_agent: str, 
                              learning_rule: str, 
                              context: Dict[str, Any] = None):
        """Add a new delegation learning pattern"""
        learning_entry = {
            "id": f"{source_agent}_to_{target_agent}_{len(self.learning_memory['delegation_patterns'])}",
            "source_agent": source_agent,
            "target_agent": target_agent,
            "learning_rule": learning_rule,
            "context": context or {},
            "created_at": datetime.now().isoformat(),
            "usage_count": 0,
            "last_used": None
        }
        
        self.learning_memory["delegation_patterns"].append(learning_entry)
        
        # Update agent sequences
        sequence_key = f"{source_agent}_to_{target_agent}"
        if sequence_key not in self.learning_memory["agent_sequences"]:
            self.learning_memory["agent_sequences"][sequence_key] = []
        
        self.learning_memory["agent_sequences"][sequence_key].append(learning_entry["id"])
        
        # Update output passing rules
        self.learning_memory["output_passing_rules"][sequence_key] = {
            "rule": learning_rule,
            "pass_output": True,
            "output_field": "output",
            "created_at": datetime.now().isoformat()
        }
        
        self._save_learning_memory()
        self.logger.info(f"Added delegation learning: {source_agent} -> {target_agent}")
    
    def get_delegation_rule(self, source_agent: str, target_agent: str) -> Optional[Dict[str, Any]]:
        """Retrieve delegation rule for specific agent sequence"""
        sequence_key = f"{source_agent}_to_{target_agent}"
        
        # Check output passing rules first
        if sequence_key in self.learning_memory["output_passing_rules"]:
            rule = self.learning_memory["output_passing_rules"][sequence_key]
            
            # Update usage statistics
            for pattern in self.learning_memory["delegation_patterns"]:
                if (pattern["source_agent"] == source_agent and 
                    pattern["target_agent"] == target_agent):
                    pattern["usage_count"] += 1
                    pattern["last_used"] = datetime.now().isoformat()
                    break
            
            self._save_learning_memory()
            return rule
        
        return None
    
    def should_pass_output(self, source_agent: str, target_agent: str) -> bool:
        """Check if output should be passed from source to target agent"""
        rule = self.get_delegation_rule(source_agent, target_agent)
        return rule.get("pass_output", False) if rule else False
    
    def get_output_field(self, source_agent: str, target_agent: str) -> str:
        """Get the field name to extract from source agent output"""
        rule = self.get_delegation_rule(source_agent, target_agent)
        return rule.get("output_field", "output") if rule else "output"
    
    def extract_agent_output(self, agent_response: Dict[str, Any], output_field: str = "output") -> str:
        """Extract output content from agent response"""
        try:
            if isinstance(agent_response, dict):
                return agent_response.get(output_field, "")
            elif isinstance(agent_response, str):
                # Try to parse as JSON if it's a string
                try:
                    parsed_response = json.loads(agent_response)
                    return parsed_response.get(output_field, agent_response)
                except json.JSONDecodeError:
                    return agent_response
            else:
                return str(agent_response)
        except Exception as e:
            self.logger.error(f"Error extracting agent output: {e}")
            return ""
    
    def format_task_with_output(self, 
                               original_task: str, 
                               source_output: str, 
                               target_agent: str) -> str:
        """Format task for target agent with source agent output"""
        try:
            # Special formatting for Social Media Publisher - pass content directly
            if target_agent == "social_publisher" or target_agent == "social_media_publisher":
                # For social media publisher, the content should be the actual content to publish
                # Extract the main content from source_output if it's formatted
                content_to_publish = source_output.strip()
                
                # If the source output contains markdown or formatting, clean it for social media
                if content_to_publish.startswith('#'):
                    # Remove markdown headers and format for social media
                    lines = content_to_publish.split('\n')
                    clean_lines = []
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Remove markdown formatting
                            line = line.replace('**', '').replace('*', '')
                            clean_lines.append(line)
                    content_to_publish = ' '.join(clean_lines[:10])  # Limit for social media
                
                return content_to_publish
            else:
                # For other agents, use the original formatting
                formatted_task = f"""
                Based on the following content created by the previous agent:
                
                {source_output}
                
                Please {original_task.lower() if original_task else 'process this content for your specific purpose'}.
                
                Use the above content as your primary input and adapt it according to your agent's specialization.
                """.strip()
                
                return formatted_task
        except Exception as e:
            self.logger.error(f"Error formatting task with output: {e}")
            return original_task
    
    def get_all_learnings(self) -> Dict[str, Any]:
        """Get all stored learnings"""
        return self.learning_memory
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get statistics about learnings"""
        total_patterns = len(self.learning_memory["delegation_patterns"])
        total_sequences = len(self.learning_memory["agent_sequences"])
        total_rules = len(self.learning_memory["output_passing_rules"])
        
        most_used = None
        max_usage = 0
        
        for pattern in self.learning_memory["delegation_patterns"]:
            if pattern["usage_count"] > max_usage:
                max_usage = pattern["usage_count"]
                most_used = f"{pattern['source_agent']} -> {pattern['target_agent']}"
        
        return {
            "total_delegation_patterns": total_patterns,
            "total_agent_sequences": total_sequences,
            "total_output_rules": total_rules,
            "most_used_pattern": most_used,
            "max_usage_count": max_usage,
            "created_at": self.learning_memory.get("created_at"),
            "last_updated": self.learning_memory.get("last_updated")
        }


# Global instance
ceo_learning_system = CEOLearningSystem()


# Initialize with the first learning rule
def initialize_first_learning():
    """Initialize the first learning rule for Content Writer -> Social Media Publisher"""
    learning_rule = (
        "When Content Writer agent completes a task and the next agent in sequence is Social Media Publisher, "
        "always pass the 'output' field from Content Writer's response to Social Media Publisher as the task content. "
        "The Social Media Publisher should receive the actual content to publish, not instructions about publishing. "
        "Format the content appropriately for social media posting, removing markdown and keeping it concise."
    )
    
    context = {
        "agent_sequence": ["content_writer", "social_media_publisher"],
        "output_field": "output",
        "task_format": "formatted_with_previous_output",
        "learning_type": "output_passing",
        "priority": "high"
    }
    
    # Check if this learning already exists
    existing_rule = ceo_learning_system.get_delegation_rule("content_writer", "social_media_publisher")
    if not existing_rule:
        ceo_learning_system.add_delegation_learning(
            source_agent="content_writer",
            target_agent="social_media_publisher",
            learning_rule=learning_rule,
            context=context
        )
        print("First learning rule initialized: Content Writer -> Social Media Publisher")
    else:
        print("Learning rule already exists for Content Writer -> Social Media Publisher")


if __name__ == "__main__":
    # Initialize the first learning when module is imported
    initialize_first_learning()
