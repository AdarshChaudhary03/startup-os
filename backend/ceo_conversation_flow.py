from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging


class ConversationState(Enum):
    """Enum for tracking conversation state"""
    INITIAL = "initial"
    GATHERING_PURPOSE = "gathering_purpose"
    GATHERING_AUDIENCE = "gathering_audience"
    GATHERING_SCOPE = "gathering_scope"
    GATHERING_CONSTRAINTS = "gathering_constraints"
    GATHERING_TIMELINE = "gathering_timeline"
    CONFIRMING_REQUIREMENTS = "confirming_requirements"
    COMPLETE = "complete"


class CEOConversationFlow:
    """Manages the conversation flow for CEO agent requirements gathering"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define the conversation flow sequence
        self.flow_sequence = [
            ConversationState.INITIAL,
            ConversationState.GATHERING_PURPOSE,
            ConversationState.GATHERING_AUDIENCE,
            ConversationState.GATHERING_SCOPE,
            ConversationState.GATHERING_CONSTRAINTS,
            ConversationState.GATHERING_TIMELINE,
            ConversationState.CONFIRMING_REQUIREMENTS,
            ConversationState.COMPLETE
        ]
        
        # Define questions for each state
        self.state_questions = {
            ConversationState.GATHERING_PURPOSE: {
                "primary": "What is the main purpose or goal of this task?",
                "follow_ups": [
                    "What specific problem are you trying to solve?",
                    "What business value will this deliver?",
                    "How will you measure success?"
                ],
                "validation": self._validate_purpose
            },
            ConversationState.GATHERING_AUDIENCE: {
                "primary": "Who is the target audience for this?",
                "follow_ups": [
                    "What are their key characteristics or demographics?",
                    "What level of technical knowledge do they have?",
                    "How will they interact with the final product?"
                ],
                "validation": self._validate_audience
            },
            ConversationState.GATHERING_SCOPE: {
                "primary": "What should be included in the scope of this project?",
                "follow_ups": [
                    "Are there any specific features or requirements?",
                    "What should NOT be included?",
                    "Are there any technical constraints or preferences?"
                ],
                "validation": self._validate_scope
            },
            ConversationState.GATHERING_CONSTRAINTS: {
                "primary": "Are there any constraints or special requirements I should be aware of?",
                "follow_ups": [
                    "Do you have any budget limitations?",
                    "Are there any compliance or regulatory requirements?",
                    "Do you have preferences for specific technologies or approaches?"
                ],
                "validation": self._validate_constraints
            },
            ConversationState.GATHERING_TIMELINE: {
                "primary": "When do you need this completed?",
                "follow_ups": [
                    "Is this timeline flexible?",
                    "Are there any milestone dates I should know about?",
                    "What is the priority level of this task?"
                ],
                "validation": self._validate_timeline
            }
        }
        
        # Question selection strategies
        self.question_strategies = {
            "adaptive": self._adaptive_question_selection,
            "comprehensive": self._comprehensive_question_selection,
            "minimal": self._minimal_question_selection
        }
    
    def get_initial_questions(self, task: str, strategy: str = "adaptive") -> List[Dict[str, Any]]:
        """Get initial questions based on task analysis and strategy"""
        
        # Analyze task to determine which areas need clarification
        missing_areas = self._analyze_task_completeness(task)
        
        # Select question strategy
        strategy_func = self.question_strategies.get(strategy, self._adaptive_question_selection)
        
        # Generate questions
        questions = strategy_func(task, missing_areas)
        
        self.logger.info(f"Generated {len(questions)} initial questions using {strategy} strategy")
        return questions
    
    def _analyze_task_completeness(self, task: str) -> List[str]:
        """Analyze task to identify missing information areas"""
        missing_areas = []
        task_lower = task.lower()
        
        # Check for purpose/goal indicators
        purpose_keywords = ["purpose", "goal", "objective", "achieve", "solve"]
        if not any(keyword in task_lower for keyword in purpose_keywords):
            missing_areas.append("purpose")
        
        # Check for audience indicators
        audience_keywords = ["for", "users", "audience", "customers", "clients"]
        if not any(keyword in task_lower for keyword in audience_keywords):
            missing_areas.append("audience")
        
        # Check for scope indicators
        scope_keywords = ["include", "feature", "requirement", "functionality"]
        if not any(keyword in task_lower for keyword in scope_keywords):
            missing_areas.append("scope")
        
        # Check for timeline indicators
        timeline_keywords = ["by", "deadline", "when", "date", "urgent", "asap"]
        if not any(keyword in task_lower for keyword in timeline_keywords):
            missing_areas.append("timeline")
        
        # Always check for constraints as they're rarely specified upfront
        missing_areas.append("constraints")
        
        return missing_areas
    
    def _adaptive_question_selection(self, task: str, missing_areas: List[str]) -> List[Dict[str, Any]]:
        """Select questions adaptively based on what's missing"""
        questions = []
        
        # Prioritize questions based on missing areas
        priority_order = ["purpose", "audience", "scope", "timeline", "constraints"]
        
        for area in priority_order:
            if area in missing_areas and len(questions) < 5:
                state = self._area_to_state(area)
                if state in self.state_questions:
                    question_data = self.state_questions[state]
                    questions.append({
                        "id": f"q_{area}_{len(questions) + 1}",
                        "area": area,
                        "question": question_data["primary"],
                        "type": "primary",
                        "required": area in ["purpose", "audience"],
                        "state": state.value
                    })
        
        # Ensure we have at least 3 questions
        if len(questions) < 3:
            # Add follow-up questions for critical areas
            for area in ["purpose", "audience"]:
                state = self._area_to_state(area)
                if state in self.state_questions and len(questions) < 5:
                    follow_ups = self.state_questions[state]["follow_ups"]
                    if follow_ups:
                        questions.append({
                            "id": f"q_{area}_followup_{len(questions) + 1}",
                            "area": area,
                            "question": follow_ups[0],
                            "type": "follow_up",
                            "required": False,
                            "state": state.value
                        })
        
        return questions[:5]  # Limit to 5 questions max
    
    def _comprehensive_question_selection(self, task: str, missing_areas: List[str]) -> List[Dict[str, Any]]:
        """Select comprehensive set of questions for thorough requirements gathering"""
        questions = []
        
        # Ask primary questions for all key areas
        for area in ["purpose", "audience", "scope", "constraints", "timeline"]:
            state = self._area_to_state(area)
            if state in self.state_questions:
                question_data = self.state_questions[state]
                questions.append({
                    "id": f"q_{area}_{len(questions) + 1}",
                    "area": area,
                    "question": question_data["primary"],
                    "type": "primary",
                    "required": area in ["purpose", "audience", "scope"],
                    "state": state.value
                })
        
        return questions
    
    def _minimal_question_selection(self, task: str, missing_areas: List[str]) -> List[Dict[str, Any]]:
        """Select minimal set of essential questions"""
        questions = []
        
        # Only ask about purpose, audience, and timeline
        essential_areas = ["purpose", "audience", "timeline"]
        
        for area in essential_areas:
            if area in missing_areas:
                state = self._area_to_state(area)
                if state in self.state_questions:
                    question_data = self.state_questions[state]
                    questions.append({
                        "id": f"q_{area}_{len(questions) + 1}",
                        "area": area,
                        "question": question_data["primary"],
                        "type": "primary",
                        "required": True,
                        "state": state.value
                    })
        
        return questions[:3]  # Limit to 3 questions
    
    def _area_to_state(self, area: str) -> ConversationState:
        """Convert area name to conversation state"""
        mapping = {
            "purpose": ConversationState.GATHERING_PURPOSE,
            "audience": ConversationState.GATHERING_AUDIENCE,
            "scope": ConversationState.GATHERING_SCOPE,
            "constraints": ConversationState.GATHERING_CONSTRAINTS,
            "timeline": ConversationState.GATHERING_TIMELINE
        }
        return mapping.get(area, ConversationState.INITIAL)
    
    def process_response(self, question_id: str, response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process user response and determine next action"""
        
        # Extract question area from ID
        area = question_id.split('_')[1] if '_' in question_id else "unknown"
        
        # Validate response
        state = self._area_to_state(area)
        is_valid = True
        validation_message = ""
        
        if state in self.state_questions:
            validation_func = self.state_questions[state].get("validation")
            if validation_func:
                is_valid, validation_message = validation_func(response)
        
        # Determine if follow-up is needed
        needs_followup = self._needs_followup(area, response, context)
        
        return {
            "question_id": question_id,
            "area": area,
            "response_valid": is_valid,
            "validation_message": validation_message,
            "needs_followup": needs_followup,
            "followup_question": self._get_followup_question(area, response) if needs_followup else None,
            "response_processed": True
        }
    
    def _validate_purpose(self, response: str) -> Tuple[bool, str]:
        """Validate purpose response"""
        if len(response.strip()) < 10:
            return False, "Please provide more detail about the purpose."
        return True, ""
    
    def _validate_audience(self, response: str) -> Tuple[bool, str]:
        """Validate audience response"""
        if len(response.strip()) < 5:
            return False, "Please specify the target audience."
        return True, ""
    
    def _validate_scope(self, response: str) -> Tuple[bool, str]:
        """Validate scope response"""
        return True, ""  # Scope can be flexible
    
    def _validate_constraints(self, response: str) -> Tuple[bool, str]:
        """Validate constraints response"""
        return True, ""  # Constraints are optional
    
    def _validate_timeline(self, response: str) -> Tuple[bool, str]:
        """Validate timeline response"""
        if "asap" in response.lower() or "urgent" in response.lower():
            return True, "Noted as urgent priority."
        return True, ""
    
    def _needs_followup(self, area: str, response: str, context: Dict[str, Any]) -> bool:
        """Determine if follow-up question is needed"""
        
        # Check response length and clarity
        if len(response.strip()) < 20 and area in ["purpose", "scope"]:
            return True
        
        # Check for vague responses
        vague_indicators = ["maybe", "not sure", "possibly", "might", "could be"]
        if any(indicator in response.lower() for indicator in vague_indicators):
            return True
        
        return False
    
    def _get_followup_question(self, area: str, response: str) -> Optional[str]:
        """Get appropriate follow-up question"""
        state = self._area_to_state(area)
        
        if state in self.state_questions:
            follow_ups = self.state_questions[state].get("follow_ups", [])
            if follow_ups:
                # Select follow-up based on response content
                if "not sure" in response.lower():
                    return follow_ups[0]  # Ask for clarification
                elif len(response) < 30:
                    return follow_ups[1] if len(follow_ups) > 1 else follow_ups[0]
                else:
                    return follow_ups[-1]  # Ask most specific question
        
        return None
    
    def generate_requirements_summary(self, responses: Dict[str, str]) -> Dict[str, Any]:
        """Generate structured requirements summary from responses"""
        
        return {
            "purpose": responses.get("purpose", "Not specified"),
            "target_audience": responses.get("audience", "General users"),
            "scope": {
                "included": responses.get("scope", "To be determined"),
                "excluded": responses.get("scope_excluded", "None specified")
            },
            "constraints": responses.get("constraints", "No specific constraints"),
            "timeline": responses.get("timeline", "Flexible"),
            "success_criteria": self._extract_success_criteria(responses),
            "priority": self._determine_priority(responses),
            "estimated_complexity": self._estimate_complexity(responses)
        }
    
    def process_user_message(self, session_id: str, message: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a user message in the chat conversation"""
        
        # Get current state from session data
        current_state = session_data.get("state", ConversationState.INITIAL)
        responses = session_data.get("responses", {})
        questions_asked = session_data.get("questions_asked", [])
        
        # Store the user's response
        if questions_asked:
            last_question = questions_asked[-1]
            area = last_question.get("area", "general")
            responses[area] = message
            session_data["responses"] = responses
        
        # Process the response and determine next action
        if questions_asked:
            process_result = self.process_response(
                question_id=last_question.get("id", "unknown"),
                response=message,
                context=session_data
            )
            
            # Check if we need a follow-up question
            if process_result.get("needs_followup") and process_result.get("followup_question"):
                followup_question = {
                    "id": f"q_followup_{len(questions_asked) + 1}",
                    "area": process_result.get("area", "general"),
                    "question": process_result["followup_question"],
                    "type": "follow_up",
                    "required": False
                }
                questions_asked.append(followup_question)
                session_data["questions_asked"] = questions_asked
                
                return {
                    "state": current_state.value if isinstance(current_state, ConversationState) else current_state,
                    "response": process_result["followup_question"],
                    "question": followup_question,
                    "requirements": self.generate_requirements_summary(responses)
                }
        
        # Determine if we have enough information
        required_areas = ["purpose", "audience"]
        has_required = all(area in responses and responses[area] for area in required_areas)
        
        # Check if we've asked enough questions (3-5 range)
        if has_required and len(questions_asked) >= 3:
            # Generate final requirements summary
            requirements = self.generate_requirements_summary(responses)
            session_data["polished_requirements"] = requirements
            session_data["state"] = ConversationState.COMPLETE
            
            return {
                "state": "requirements_complete",
                "response": "Thank you! I've gathered all the necessary information. Here's a summary of your requirements:",
                "requirements": requirements
            }
        
        # Get next question if we need more information
        remaining_questions = []
        if len(questions_asked) < 5:
            # Get questions we haven't asked yet
            asked_areas = [q.get("area") for q in questions_asked]
            for area in ["purpose", "audience", "scope", "timeline", "constraints"]:
                if area not in asked_areas:
                    state = self._area_to_state(area)
                    if state in self.state_questions:
                        question_data = self.state_questions[state]
                        remaining_questions.append({
                            "id": f"q_{area}_{len(questions_asked) + 1}",
                            "area": area,
                            "question": question_data["primary"],
                            "type": "primary",
                            "required": area in required_areas
                        })
        
        if remaining_questions:
            # Ask the next question
            next_question = remaining_questions[0]
            questions_asked.append(next_question)
            session_data["questions_asked"] = questions_asked
            
            return {
                "state": self._area_to_state(next_question["area"]).value,
                "response": next_question["question"],
                "question": next_question,
                "requirements": self.generate_requirements_summary(responses)
            }
        
        # If we've asked enough questions but don't have required info, wrap up
        requirements = self.generate_requirements_summary(responses)
        session_data["polished_requirements"] = requirements
        session_data["state"] = ConversationState.COMPLETE
        
        return {
            "state": "requirements_complete",
            "response": "I've gathered the available information. Let me create a plan based on what you've shared.",
            "requirements": requirements
        }
    
    async def finalize_requirements(self, session_id: str, session_data: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Finalize requirements and prepare for plan creation"""
        
        responses = session_data.get("responses", {})
        requirements = self.generate_requirements_summary(responses)
        
        # Import simplified CEO agent
        from ceo_simplified_flow import simplified_ceo_agent
        
        # Create polished requirements prompt
        polished_prompt = simplified_ceo_agent.format_requirements({
            "original_task": session_data.get("original_task", "Task not specified"),
            "purpose": requirements.get("purpose", "Not specified"),
            "target_audience": requirements.get("target_audience", "General users"),
            "scope": requirements.get("scope", {}),
            "constraints": requirements.get("constraints", "None"),
            "timeline": requirements.get("timeline", "Flexible"),
            "success_criteria": requirements.get("success_criteria", [])
        })
        
        # Log the finalization process
        self.logger.info(f"[CEO_CHAT_DEBUG] Finalizing requirements for session {session_id}")
        self.logger.info(f"[CEO_CHAT_DEBUG] Original task: {session_data.get('original_task', 'Not specified')}")
        self.logger.info(f"[CEO_CHAT_DEBUG] Polished prompt: {polished_prompt}")
        
        # Get orchestration plan using simplified flow
        orchestration_result = None
        try:
            self.logger.info(f"[CEO_CHAT_DEBUG] Getting orchestration plan...")
            orchestration_result = await simplified_ceo_agent.get_orchestration_plan(
                polished_requirements=polished_prompt,
                session_id=session_id
            )
            self.logger.info(f"[CEO_CHAT_DEBUG] Orchestration plan received: {orchestration_result}")
            self.logger.info(f"[CEO_CHAT_DEBUG] Orchestration mode: {orchestration_result.get('mode', 'UNDEFINED')}")
            self.logger.info(f"[CEO_CHAT_DEBUG] Orchestration steps: {len(orchestration_result.get('steps', []))}")
            
        except Exception as e:
            self.logger.error(f"[CEO_CHAT_DEBUG] Failed to get orchestration plan: {e}")
            orchestration_result = {
                "error": "Failed to get orchestration plan",
                "details": str(e)
            }
        
        # Create result structure
        result = {
            "requirements": requirements,
            "polished_prompt": polished_prompt,
            "orchestration_result": orchestration_result,
            "success": orchestration_result is not None and "error" not in orchestration_result,
            "ready_for_execution": orchestration_result is not None and "steps" in orchestration_result
        }
        
        self.logger.info(f"[CEO_CHAT_DEBUG] Final result being returned: {result}")
        self.logger.info(f"[CEO_CHAT_DEBUG] Ready for execution: {result.get('ready_for_execution')}")
        
        return result
    
    def _extract_success_criteria(self, responses: Dict[str, str]) -> List[str]:
        """Extract success criteria from responses"""
        criteria = []
        
        purpose = responses.get("purpose", "")
        if "increase" in purpose.lower():
            criteria.append("Measurable increase in target metric")
        if "improve" in purpose.lower():
            criteria.append("Demonstrable improvement over current state")
        if "create" in purpose.lower() or "build" in purpose.lower():
            criteria.append("Successful delivery of working solution")
        
        # Add audience-specific criteria
        audience = responses.get("audience", "")
        if audience:
            criteria.append(f"Positive feedback from {audience}")
        
        return criteria if criteria else ["Task completed successfully"]
    
    def _determine_priority(self, responses: Dict[str, str]) -> str:
        """Determine priority based on responses"""
        timeline = responses.get("timeline", "").lower()
        
        if any(word in timeline for word in ["urgent", "asap", "immediately", "critical"]):
            return "urgent"
        elif any(word in timeline for word in ["soon", "quickly", "priority"]):
            return "high"
        elif any(word in timeline for word in ["flexible", "whenever", "no rush"]):
            return "low"
        else:
            return "normal"
    
    def _estimate_complexity(self, responses: Dict[str, str]) -> str:
        """Estimate task complexity based on responses"""
        scope = responses.get("scope", "").lower()
        constraints = responses.get("constraints", "").lower()
        
        complexity_score = 0
        
        # Check scope complexity
        if any(word in scope for word in ["multiple", "complex", "integrated", "comprehensive"]):
            complexity_score += 2
        
        # Check constraint complexity
        if any(word in constraints for word in ["strict", "compliance", "security", "performance"]):
            complexity_score += 2
        
        # Check audience complexity
        audience = responses.get("audience", "").lower()
        if any(word in audience for word in ["technical", "enterprise", "global", "diverse"]):
            complexity_score += 1
        
        if complexity_score >= 4:
            return "high"
        elif complexity_score >= 2:
            return "medium"
        else:
            return "low"
    
    def _extract_deliverables_from_requirements(self, requirements: Dict[str, Any]) -> List[str]:
        """Extract deliverables from requirements summary"""
        deliverables = []
        
        # Extract from scope
        scope = requirements.get("scope", {})
        if isinstance(scope, dict) and "included" in scope:
            included = scope["included"]
            if isinstance(included, str):
                deliverables.extend([item.strip() for item in included.split(",") if item.strip()])
        
        # Extract from purpose
        purpose = requirements.get("purpose", "")
        if "create" in purpose.lower() or "build" in purpose.lower():
            deliverables.append("Completed implementation as per requirements")
        
        # Add default deliverable if none found
        if not deliverables:
            deliverables.append("Complete the requested task as specified")
        
        return deliverables


# Export the conversation flow manager
ceo_conversation_flow = CEOConversationFlow()
