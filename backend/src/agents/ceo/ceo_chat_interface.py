from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import uuid
import logging
from enum import Enum

from src.core.models import (
    CEORequirementsRequest,
    CEORequirementsResponse,
    CEOClarificationRequest,
    CEOPolishedRequirement
)
from .ceo_conversation_flow import ceo_conversation_flow, ConversationState


class ChatSessionState(Enum):
    """States for chat session"""
    INITIALIZING = "initializing"
    ASKING_QUESTIONS = "asking_questions"
    AWAITING_RESPONSE = "awaiting_response"
    PROCESSING_RESPONSE = "processing_response"
    CONFIRMING_REQUIREMENTS = "confirming_requirements"
    FINALIZING = "finalizing"
    COMPLETE = "complete"


class CEOChatInterface:
    """Interactive chat interface for CEO agent requirements gathering"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.conversation_flow = ceo_conversation_flow
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_history: Dict[str, List[Dict[str, Any]]] = {}
    
    async def start_chat_session(self, task: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Start a new chat session for requirements gathering"""
        
        session_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())
        
        # Initialize session
        session_data = {
            "session_id": session_id,
            "request_id": request_id,
            "original_task": task,
            "user_context": user_context or {},
            "state": ChatSessionState.INITIALIZING,
            "conversation_state": ConversationState.INITIAL,
            "responses": {},
            "questions_asked": [],
            "current_question": None,
            "question_count": 0,
            "max_questions": 5,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "answers": {},
            "current_question_index": 0,
            "questions": []
        }
        
        self.active_sessions[session_id] = session_data
        self.session_history[session_id] = []
        
        # Log session start
        self._log_chat_event(session_id, "session_started", {
            "task": task,
            "user_context": user_context
        })
        
        # Generate initial greeting
        greeting = self._generate_greeting(task)
        
        # Use AI-driven conversation flow to analyze task and get questions
        try:
            ai_result = await self.conversation_flow.process_user_message(session_id, task, session_data)
            
            # Update session based on AI result with null checks
            if ai_result and ai_result.get("state") == ConversationState.AI_QUESTIONING.value:
                session_data["state"] = ChatSessionState.ASKING_QUESTIONS
                session_data["questions"] = ai_result.get("questions", []) if ai_result.get("questions") is not None else []
                session_data["current_question_index"] = 0
                initial_questions = ai_result.get("questions", []) if ai_result.get("questions") is not None else []
            elif ai_result:
                # Task is already complete
                session_data["state"] = ChatSessionState.COMPLETE
                session_data["polished_prompt"] = ai_result.get("polished_prompt")
                initial_questions = []
            else:
                # AI result is None, handle gracefully
                session_data["state"] = ChatSessionState.ASKING_QUESTIONS
                initial_questions = []
            
            session_data["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            return {
                "session_id": session_id,
                "greeting": greeting,
                "initial_questions": initial_questions,
                "state": session_data["state"].value,
                "max_questions": session_data["max_questions"],
                "ai_analysis": ai_result.get("analysis") if ai_result else {}
            }
        except Exception as e:
            self.logger.error(f"Failed to start chat session with AI: {e}")
            # Fallback to simple response
            session_data["state"] = ChatSessionState.ASKING_QUESTIONS
            return {
                "session_id": session_id,
                "greeting": greeting,
                "initial_questions": [],
                "state": session_data["state"].value,
                "max_questions": session_data["max_questions"],
                "error": str(e)
            }
    
    async def process_user_response(self, session_id: str, question_id: str, response: str) -> Dict[str, Any]:
        """Process user response to a question"""
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        # Update state
        session["state"] = ChatSessionState.PROCESSING_RESPONSE
        session["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Store response
        session["responses"][question_id] = response
        session["questions_asked"].append(question_id)
        session["question_count"] += 1
        
        # Log response
        self._log_chat_event(session_id, "response_received", {
            "question_id": question_id,
            "response": response
        })
        
        # Process response through AI conversation flow
        try:
            ai_result = await self.conversation_flow.process_user_message(session_id, response, session)
            
            # Update session based on AI result
            if ai_result.get("state") == ConversationState.AI_QUESTIONING.value:
                session["state"] = ChatSessionState.ASKING_QUESTIONS
                if "questions" in ai_result:
                    session["questions"] = ai_result["questions"]
                if "current_question_index" in ai_result:
                    session["current_question_index"] = ai_result["current_question_index"]
                
                return {
                    "action": "ask_next",
                    "question": {
                        "id": f"q_{session['current_question_index']}",
                        "question": ai_result["response"]
                    },
                    "message": "Let me ask you about another aspect.",
                    "questions_remaining": len(session.get("questions", [])) - session.get("current_question_index", 0),
                    "ai_analysis": ai_result.get("analysis")
                }
            elif ai_result.get("state") == ConversationState.COMPLETE.value:
                session["state"] = ChatSessionState.CONFIRMING_REQUIREMENTS
                session["polished_prompt"] = ai_result.get("polished_prompt")
                
                return {
                    "action": "confirm_requirements",
                    "requirements_summary": {
                        "polished_prompt": ai_result.get("polished_prompt"),
                        "analysis": ai_result.get("analysis")
                    },
                    "message": ai_result["response"],
                    "next_step": "Please review and confirm these requirements."
                }
            else:
                # Continue with questions
                return {
                    "action": "continue",
                    "message": ai_result.get("response", "Processing your response...")
                }
        except Exception as e:
            self.logger.error(f"Failed to process response with AI: {e}")
            # Fallback to simple acknowledgment
            return {
                "action": "error",
                "message": "I encountered an issue processing your response. Let's continue.",
                "error": str(e)
            }
    
    def _determine_next_action(self, session: Dict[str, Any], process_result: Dict[str, Any]) -> Dict[str, Any]:
        """Determine next action based on session state and response processing"""
        
        # Check if we need a follow-up question
        if process_result.get("needs_followup") and session["question_count"] < session["max_questions"]:
            followup_question = process_result.get("followup_question")
            if followup_question:
                followup_obj = {
                    "id": f"q_followup_{session['question_count'] + 1}",
                    "question": followup_question,
                    "area": process_result.get("area", "general"),
                    "type": "follow_up",
                    "required": False
                }
                
                session["state"] = ChatSessionState.ASKING_QUESTIONS
                session["current_question"] = followup_obj
                
                return {
                    "action": "ask_followup",
                    "question": followup_obj,
                    "message": "I need a bit more clarification on this point.",
                    "questions_remaining": session["max_questions"] - session["question_count"]
                }
        
        # Check if we have more pending questions
        pending_questions = session.get("pending_questions", [])
        unanswered_questions = [
            q for q in pending_questions 
            if q["id"] not in session["questions_asked"]
        ]
        
        if unanswered_questions and session["question_count"] < session["max_questions"]:
            next_question = unanswered_questions[0]
            session["state"] = ChatSessionState.ASKING_QUESTIONS
            session["current_question"] = next_question
            
            return {
                "action": "ask_next",
                "question": next_question,
                "message": self._get_transition_message(session["question_count"]),
                "questions_remaining": session["max_questions"] - session["question_count"]
            }
        
        # Check if we have enough information to proceed
        if self._has_sufficient_information(session):
            session["state"] = ChatSessionState.CONFIRMING_REQUIREMENTS
            requirements_summary = self._generate_requirements_summary(session)
            
            return {
                "action": "confirm_requirements",
                "requirements_summary": requirements_summary,
                "message": "Based on our conversation, here's what I understand about your requirements:",
                "next_step": "Please review and confirm these requirements, or let me know if anything needs adjustment."
            }
        
        # If we've asked max questions but still need info, wrap up
        if session["question_count"] >= session["max_questions"]:
            session["state"] = ChatSessionState.CONFIRMING_REQUIREMENTS
            requirements_summary = self._generate_requirements_summary(session)
            
            return {
                "action": "max_questions_reached",
                "requirements_summary": requirements_summary,
                "message": "I've gathered as much information as I can with our question limit. Here's what I understand:",
                "next_step": "Please review these requirements and let me know if they capture your needs."
            }
        
        # Default: ask for more details
        return {
            "action": "need_more_info",
            "message": "I need a bit more information to create comprehensive requirements.",
            "suggestion": "Could you provide more details about your specific needs?"
        }
    
    async def confirm_requirements(self, session_id: str, confirmed: bool, adjustments: Optional[str] = None) -> Dict[str, Any]:
        """Handle requirements confirmation"""
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        if confirmed:
            session["state"] = ChatSessionState.FINALIZING
            
            # Get polished prompt from AI analysis or generate requirements
            if "polished_prompt" in session:
                polished_requirements = CEOPolishedRequirement(
                    polished_task=session["polished_prompt"],
                    objective="AI-analyzed task objectives",
                    target_audience="As identified by AI analysis",
                    deliverables=["Complete the task as specified in the polished prompt"],
                    success_criteria=["Task completed according to AI-refined requirements"],
                    constraints=["No specific constraints"],
                    timeline="Flexible",
                    additional_context="AI-driven analysis completed",
                    agent_plan_suggestion="Use appropriate agents based on task requirements"
                )
            else:
                # Fallback to traditional requirements polishing
                polished_requirements = self._polish_requirements(session)
            
            session["state"] = ChatSessionState.COMPLETE
            session["polished_requirements"] = polished_requirements
            session["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            # Log completion
            self._log_chat_event(session_id, "requirements_confirmed", {
                "polished_requirements": polished_requirements
            })
            
            return {
                "action": "requirements_complete",
                "polished_requirements": polished_requirements,
                "message": "Perfect! I've finalized your requirements and they're ready for the next phase.",
                "next_step": "proceed_to_agent_planning"
            }
        else:
            # Handle adjustments
            if adjustments:
                session["responses"]["adjustments"] = adjustments
                
                # Re-analyze with adjustments through AI
                try:
                    # Add adjustments to the conversation and re-process
                    ai_result = await self.conversation_flow.process_user_message(
                        session_id, 
                        f"Please adjust the requirements with these changes: {adjustments}", 
                        session
                    )
                    
                    if ai_result.get("polished_prompt"):
                        session["polished_prompt"] = ai_result["polished_prompt"]
                    
                    return {
                        "action": "requirements_adjusted",
                        "requirements_summary": {
                            "polished_prompt": ai_result.get("polished_prompt"),
                            "analysis": ai_result.get("analysis")
                        },
                        "message": "I've updated the requirements based on your feedback.",
                        "next_step": "Please review the updated requirements."
                    }
                except Exception as e:
                    self.logger.error(f"Failed to process adjustments with AI: {e}")
                    # Fallback to traditional summary
                    updated_summary = self._generate_requirements_summary(session)
                    return {
                        "action": "requirements_adjusted",
                        "requirements_summary": updated_summary,
                        "message": "I've updated the requirements based on your feedback.",
                        "next_step": "Please review the updated requirements."
                    }
            else:
                return {
                    "action": "need_adjustments",
                    "message": "Please let me know what adjustments you'd like to make to the requirements."
                }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current status of a chat session"""
        
        if session_id not in self.active_sessions:
            return {
                "status": "not_found",
                "message": f"Session {session_id} not found"
            }
        
        session = self.active_sessions[session_id]
        
        return {
            "session_id": session_id,
            "state": session["state"].value,
            "questions_asked": len(session["questions_asked"]),
            "max_questions": session["max_questions"],
            "responses_collected": len(session["responses"]),
            "current_question": session.get("current_question"),
            "created_at": session["created_at"],
            "updated_at": session["updated_at"],
            "is_complete": session["state"] == ChatSessionState.COMPLETE
        }
    
    def _generate_greeting(self, task: str) -> str:
        """Generate personalized greeting for the chat session"""
        
        task_preview = task[:100] + "..." if len(task) > 100 else task
        
        greetings = [
            f"Hello! I'm the CEO agent, and I'll help you create clear requirements for: '{task_preview}'. I'll ask you a few questions to better understand your needs.",
            f"Welcome! I see you need help with: '{task_preview}'. Let me ask you some questions to ensure I understand exactly what you're looking for.",
            f"Hi there! I'm here to help you define requirements for your task. I'll guide you through a few questions to make sure we capture everything correctly."
        ]
        
        # Select greeting based on task length/complexity
        if len(task) < 50:
            return greetings[1]  # Short task, needs more detail
        elif len(task) > 200:
            return greetings[2]  # Long task, already detailed
        else:
            return greetings[0]  # Medium task, balanced approach
    
    def _get_transition_message(self, question_count: int) -> str:
        """Get appropriate transition message between questions"""
        
        transitions = [
            "Great! Let me ask you about another aspect.",
            "Thank you for that information. Moving on...",
            "Perfect! I have another question for you.",
            "That's helpful! Let's talk about...",
            "Excellent! One more thing I'd like to understand..."
        ]
        
        # Use different transitions based on progress
        if question_count == 0:
            return "Let's start with the first question."
        elif question_count >= 4:
            return "Almost done! Just one more question."
        else:
            return transitions[question_count % len(transitions)]
    
    def _has_sufficient_information(self, session: Dict[str, Any]) -> bool:
        """Check if we have sufficient information to proceed"""
        
        responses = session.get("responses", {})
        
        # Check if we have responses for required areas
        required_areas = ["purpose", "audience"]
        has_required = any(
            area in str(response_key) 
            for area in required_areas 
            for response_key in responses.keys()
        )
        
        # Need at least 3 responses or all required areas covered
        return len(responses) >= 3 and has_required
    
    def _generate_requirements_summary(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Generate requirements summary from collected responses"""
        
        responses = session.get("responses", {})
        
        # Map responses to requirement areas
        mapped_responses = {}
        for question_id, response in responses.items():
            if "purpose" in question_id:
                mapped_responses["purpose"] = response
            elif "audience" in question_id:
                mapped_responses["audience"] = response
            elif "scope" in question_id:
                mapped_responses["scope"] = response
            elif "timeline" in question_id:
                mapped_responses["timeline"] = response
            elif "constraints" in question_id:
                mapped_responses["constraints"] = response
            else:
                mapped_responses[question_id] = response
        
        # Use conversation flow to generate summary
        return self.conversation_flow.generate_requirements_summary(mapped_responses)
    
    def _polish_requirements(self, session: Dict[str, Any]) -> CEOPolishedRequirement:
        """Generate polished requirements from session data"""
        
        summary = self._generate_requirements_summary(session)
        
        # Create polished requirement object
        polished = CEOPolishedRequirement(
            polished_task=self._create_polished_task_description(session, summary),
            objective=summary.get("purpose", "Not specified"),
            target_audience=summary.get("target_audience", "General users"),
            deliverables=self._extract_deliverables(summary),
            success_criteria=summary.get("success_criteria", ["Task completed successfully"]),
            constraints=self._extract_constraints(summary),
            timeline=summary.get("timeline", "Flexible"),
            additional_context=self._compile_additional_context(session),
            agent_plan_suggestion=self._suggest_agent_plan(summary)
        )
        
        return polished
    
    def _create_polished_task_description(self, session: Dict[str, Any], summary: Dict[str, Any]) -> str:
        """Create polished task description"""
        
        original_task = session.get("original_task", "")
        purpose = summary.get("purpose", "")
        audience = summary.get("target_audience", "")
        
        polished = f"{original_task}\n\n"
        polished += f"Purpose: {purpose}\n"
        polished += f"Target Audience: {audience}\n"
        
        if summary.get("scope"):
            polished += f"Scope: {summary['scope'].get('included', 'To be determined')}\n"
        
        return polished.strip()
    
    def _extract_deliverables(self, summary: Dict[str, Any]) -> List[str]:
        """Extract deliverables from summary"""
        
        deliverables = []
        
        # Extract from scope
        scope = summary.get("scope", {})
        if isinstance(scope, dict) and "included" in scope:
            # Parse included items as deliverables
            included = scope["included"]
            if isinstance(included, str):
                deliverables.extend([item.strip() for item in included.split(",") if item.strip()])
        
        # Add default deliverable if none found
        if not deliverables:
            deliverables.append("Complete the requested task as specified")
        
        return deliverables
    
    def _extract_constraints(self, summary: Dict[str, Any]) -> List[str]:
        """Extract constraints from summary"""
        
        constraints = []
        
        constraints_text = summary.get("constraints", "")
        if constraints_text and constraints_text != "No specific constraints":
            constraints.extend([c.strip() for c in constraints_text.split(",") if c.strip()])
        
        # Add timeline as constraint if urgent
        priority = summary.get("priority", "")
        if priority in ["urgent", "high"]:
            constraints.append(f"High priority - {priority} timeline")
        
        return constraints if constraints else ["No specific constraints"]
    
    def _compile_additional_context(self, session: Dict[str, Any]) -> str:
        """Compile additional context from session"""
        
        context_parts = []
        
        # Add user context if provided
        user_context = session.get("user_context", {})
        if user_context:
            context_parts.append(f"User Context: {str(user_context)}")
        
        # Add any adjustment responses
        if "adjustments" in session.get("responses", {}):
            context_parts.append(f"Adjustments: {session['responses']['adjustments']}")
        
        # Add session metadata
        context_parts.append(f"Questions asked: {len(session.get('questions_asked', []))}")
        context_parts.append(f"Session duration: {self._calculate_session_duration(session)}")
        
        return "\n".join(context_parts)
    
    def _suggest_agent_plan(self, summary: Dict[str, Any]) -> str:
        """Suggest which agents to use based on requirements"""
        
        suggestions = []
        
        purpose = summary.get("purpose", "").lower()
        
        # Content creation agents
        if any(word in purpose for word in ["write", "content", "article", "blog", "copy"]):
            suggestions.append("Content Writer Agent")
        
        # Social media agents
        if any(word in purpose for word in ["social", "post", "instagram", "twitter", "linkedin"]):
            suggestions.append("Social Media Publisher Agent")
        
        # Technical agents
        if any(word in purpose for word in ["code", "develop", "program", "test", "debug"]):
            suggestions.extend(["Unit Test Agent", "PR Agent", "Sonar Agent"])
        
        # Default suggestion
        if not suggestions:
            suggestions.append("Appropriate specialized agent based on task type")
        
        return ", ".join(suggestions)
    
    def _calculate_session_duration(self, session: Dict[str, Any]) -> str:
        """Calculate session duration"""
        
        try:
            created = datetime.fromisoformat(session["created_at"].replace('Z', '+00:00'))
            updated = datetime.fromisoformat(session["updated_at"].replace('Z', '+00:00'))
            duration = updated - created
            
            minutes = int(duration.total_seconds() / 60)
            if minutes < 1:
                return "Less than 1 minute"
            elif minutes == 1:
                return "1 minute"
            else:
                return f"{minutes} minutes"
        except:
            return "Duration unknown"
    
    def _log_chat_event(self, session_id: str, event_type: str, data: Dict[str, Any]):
        """Log chat event to session history"""
        
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "data": data
        }
        
        if session_id not in self.session_history:
            self.session_history[session_id] = []
        
        self.session_history[session_id].append(event)
        self.logger.info(f"Chat event: {event_type} for session {session_id}")


# Create global instance
ceo_chat_interface = CEOChatInterface()
