from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
from .ceo_ai_task_analyzer import ceo_ai_task_analyzer


class ConversationState(Enum):
    """Enum for tracking conversation state"""
    INITIAL = "initial"
    AI_ANALYZING = "ai_analyzing"
    AI_QUESTIONING = "ai_questioning"
    AI_REFINING = "ai_refining"
    COMPLETE = "complete"


class CEOConversationFlow:
    """Manages the AI-driven conversation flow for CEO agent requirements gathering"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ai_analyzer = ceo_ai_task_analyzer
        self.current_analysis_session = None
    
    async def analyze_task_with_ai(self, task: str, session_id: str) -> Dict[str, Any]:
        """Use AI to analyze task and generate questions if needed"""
        
        self.logger.info(f"[CEO_AI_FLOW] Starting AI-based task analysis for session {session_id}")
        
        # Use the AI task analyzer
        analysis_result = await self.ai_analyzer.analyze_task(task, session_id)
        
        # Store the current analysis session
        self.current_analysis_session = {
            "session_id": session_id,
            "task": task,
            "analysis_result": analysis_result
        }
        
        return analysis_result
    
    async def continue_analysis_with_answers(self, answers: Dict[str, str]) -> Dict[str, Any]:
        """Continue AI analysis with user answers"""
        
        if not self.current_analysis_session:
            raise ValueError("No active analysis session found")
        
        session_data = self.current_analysis_session["analysis_result"]
        
        # Continue with AI analyzer
        result = await self.ai_analyzer.continue_with_answers(session_data, answers)
        
        # Update session
        self.current_analysis_session["analysis_result"] = result
        
        return result
    
    def get_current_state(self) -> ConversationState:
        """Get current conversation state based on AI analysis"""
        if not self.current_analysis_session:
            return ConversationState.INITIAL
        
        analysis_state = self.current_analysis_session["analysis_result"].get("state")
        
        if analysis_state == "awaiting_answers":
            return ConversationState.AI_QUESTIONING
        elif analysis_state == "complete":
            return ConversationState.COMPLETE
        elif analysis_state in ["restructuring", "re_analyzing"]:
            return ConversationState.AI_REFINING
        else:
            return ConversationState.AI_ANALYZING
    
    def format_questions_for_display(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format AI-generated questions for display to user"""
        formatted_questions = []
        
        for q in questions:
            formatted_questions.append({
                "id": q.get("id"),
                "question": q.get("question"),
                "purpose": q.get("purpose"),
                "category": q.get("category"),
                "priority": q.get("priority"),
                "required": q.get("priority") == "high"
            })
        
        return formatted_questions
    
    def get_polished_prompt(self) -> Optional[str]:
        """Get the polished prompt from AI analysis"""
        if not self.current_analysis_session:
            return None
        
        result = self.current_analysis_session["analysis_result"]
        if result.get("state") == "complete":
            return result.get("polished_prompt")
        
        return None
    
    async def process_user_message(self, session_id: str, message: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a user message using AI-driven conversation flow"""
        
        # Validate session_data is not None
        if session_data is None:
            self.logger.error(f"[CEO_AI_FLOW] Session data is None for session {session_id}")
            return {
                "state": "error",
                "response": "Session data is missing. Please restart the chat.",
                "error": "Session data is None"
            }
        
        # Check if user is confirming the polished prompt
        if session_data.get("state") == "awaiting_confirmation":
            # User is responding to confirmation request
            if any(word in message.lower() for word in ["yes", "confirm", "proceed", "correct", "looks good", "go ahead"]):
                # User confirmed - proceed to orchestration
                self.logger.info(f"[CEO_AI_FLOW] User confirmed polished prompt, proceeding to orchestration")
                
                # Get the polished prompt from session data
                polished_prompt = session_data.get("polished_prompt")
                
                # CRITICAL FIX: If polished_prompt is not in session_data, get it from current analysis
                if not polished_prompt:
                    polished_prompt = self.get_polished_prompt()
                    self.logger.info(f"[CEO_AI_FLOW] Retrieved polished prompt from current analysis")
                
                if not polished_prompt:
                    self.logger.error(f"[CEO_AI_FLOW] No polished prompt available for orchestration")
                    return {
                        "state": "error",
                        "response": "I'm sorry, but I couldn't find the polished prompt. Let me restart the process.",
                        "error": "Polished prompt not found"
                    }
                
                # Import simplified CEO agent for orchestration
                from .ceo_simplified_flow import simplified_ceo_agent
                
                try:
                    # Get orchestration plan
                    orchestration_result = await simplified_ceo_agent.get_orchestration_plan(
                        polished_requirements=polished_prompt,
                        session_id=session_id
                    )
                    
                    return {
                        "state": ConversationState.COMPLETE.value,
                        "response": "Great! I'm now creating a plan for agent delegation based on your confirmed requirements.",
                        "orchestration_started": True,
                        "orchestration_result": orchestration_result,
                        "polished_prompt": polished_prompt,
                        "task": polished_prompt  # Add task field for API compatibility
                    }
                except Exception as e:
                    self.logger.error(f"[CEO_AI_FLOW] Failed to start orchestration: {e}")
                    return {
                        "state": "error",
                        "response": f"I encountered an error while starting the orchestration: {str(e)}. Please try again.",
                        "error": str(e)
                    }
            else:
                # User wants to modify - restart the analysis
                self.logger.info(f"[CEO_AI_FLOW] User wants to modify requirements")
                return {
                    "state": ConversationState.INITIAL.value,
                    "response": "I understand you'd like to modify the requirements. Please provide your updated task description, and I'll analyze it again.",
                    "restart": True
                }
        
        # Check if this is the initial task or a response to questions
        if not self.current_analysis_session or (session_data and session_data.get("state") == ConversationState.INITIAL):
            # Initial task analysis
            self.logger.info(f"[CEO_AI_FLOW] Processing initial task: {message[:100]}...")
            analysis_result = await self.analyze_task_with_ai(message, session_id)
            
            if analysis_result.get("requires_user_input"):
                # AI needs more information
                questions = analysis_result.get("questions", [])
                formatted_questions = self.format_questions_for_display(questions)
                
                return {
                    "state": ConversationState.AI_QUESTIONING.value,
                    "response": formatted_questions[0]["question"] if formatted_questions else "Could you provide more details?",
                    "questions": formatted_questions,
                    "analysis": {
                        "completeness_score": analysis_result.get("completeness_score"),
                        "iteration": analysis_result.get("iteration")
                    }
                }
            else:
                # Task analysis is complete - show polished prompt for confirmation
                polished_prompt = analysis_result.get("polished_prompt")
                executive_summary = analysis_result.get("executive_summary", "")
                deliverables = analysis_result.get("deliverables", [])
                
                # Format the polished prompt for display
                formatted_response = f"""I've analyzed and refined your task. Here's the polished prompt:

**Polished Task Description:**
{polished_prompt}

**Executive Summary:**
{executive_summary}

**Key Deliverables:**
{chr(10).join(f'- {d}' for d in deliverables) if deliverables else 'No specific deliverables identified'}

**Would you like to proceed with this refined task description?** Please confirm if this accurately captures your requirements, or let me know if you'd like to make any adjustments."""
                
                return {
                    "state": "awaiting_confirmation",
                    "response": formatted_response,
                    "polished_prompt": polished_prompt,
                    "executive_summary": executive_summary,
                    "deliverables": deliverables,
                    "analysis": {
                        "final_score": analysis_result.get("final_completeness_score"),
                        "iterations": analysis_result.get("iterations_used")
                    },
                    "requires_confirmation": True
                }
        else:
            # This is a response to AI questions
            self.logger.info(f"[CEO_AI_FLOW] Processing user answers")
            
            # Collect answers from the current question
            questions = session_data.get("questions", [])
            answers = session_data.get("answers", {})
            current_question_index = session_data.get("current_question_index", 0)
            
            if current_question_index < len(questions):
                current_question = questions[current_question_index]
                answers[current_question["id"]] = message
                session_data["answers"] = answers
                session_data["current_question_index"] = current_question_index + 1
                
                # Immediately re-analyze after each answer instead of asking all questions
                # This allows us to stop early if completeness score reaches 6
                # Single question answered, check if we need to continue
                # Re-analyze after each answer instead of waiting for all questions
                analysis_result = await self.continue_analysis_with_answers(answers)
                
                if analysis_result.get("requires_user_input"):
                    # Need more clarification
                    new_questions = analysis_result.get("questions", [])
                    formatted_questions = self.format_questions_for_display(new_questions)
                    session_data["questions"] = formatted_questions
                    session_data["current_question_index"] = 0
                    session_data["answers"] = {}
                    
                    return {
                        "state": ConversationState.AI_QUESTIONING.value,
                        "response": formatted_questions[0]["question"] if formatted_questions else "Could you clarify further?",
                        "questions": formatted_questions,
                        "analysis": {
                            "completeness_score": analysis_result.get("completeness_score"),
                            "iteration": analysis_result.get("iteration")
                        }
                    }
                else:
                    # Analysis complete - show polished prompt for confirmation
                    polished_prompt = analysis_result.get("polished_prompt")
                    executive_summary = analysis_result.get("executive_summary", "")
                    deliverables = analysis_result.get("deliverables", [])
                    
                    # Format the polished prompt for display
                    formatted_response = f"""Perfect! I've refined your task based on your answers. Here's the polished prompt:

**Polished Task Description:**
{polished_prompt}

**Executive Summary:**
{executive_summary}

**Key Deliverables:**
{chr(10).join(f'- {d}' for d in deliverables) if deliverables else 'No specific deliverables identified'}

**Would you like to proceed with this refined task description?** Please confirm if this accurately captures your requirements, or let me know if you'd like to make any adjustments."""
                    
                    return {
                        "state": "awaiting_confirmation",
                        "response": formatted_response,
                        "polished_prompt": polished_prompt,
                        "executive_summary": executive_summary,
                        "deliverables": deliverables,
                        "analysis": {
                            "final_score": analysis_result.get("final_completeness_score"),
                            "iterations": analysis_result.get("iterations_used")
                        },
                        "requires_confirmation": True
                    }
    
    async def finalize_requirements(self, session_id: str, session_data: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Finalize requirements and prepare for plan creation using AI-generated prompt"""
        
        # Get the polished prompt from AI analysis
        polished_prompt = self.get_polished_prompt()
        
        if not polished_prompt:
            self.logger.error(f"[CEO_AI_FLOW] No polished prompt available for session {session_id}")
            return {
                "success": False,
                "error": "No polished prompt available from AI analysis"
            }
        
        # Import simplified CEO agent
        from .ceo_simplified_flow import simplified_ceo_agent
        
        # Log the finalization process
        self.logger.info(f"[CEO_AI_FLOW] Finalizing requirements for session {session_id}")
        self.logger.info(f"[CEO_AI_FLOW] Using AI-generated polished prompt")
        
        # Get orchestration plan using simplified flow
        orchestration_result = None
        try:
            # Validate polished prompt before sending
            if not polished_prompt:
                raise ValueError("Polished prompt is None or empty - cannot proceed with orchestration")
                
            self.logger.info(f"[CEO_AI_FLOW] Getting orchestration plan...")
            self.logger.info(f"[CEO_AI_FLOW] Polished prompt to send: {polished_prompt[:200]}...")
            
            orchestration_result = await simplified_ceo_agent.get_orchestration_plan(
                polished_requirements=polished_prompt,
                session_id=session_id
            )
            self.logger.info(f"[CEO_AI_FLOW] Orchestration plan received")
            
        except ValueError as ve:
            self.logger.error(f"[CEO_AI_FLOW] Validation error: {ve}")
            orchestration_result = {
                "error": "Validation failed",
                "details": str(ve)
            }
        except Exception as e:
            self.logger.error(f"[CEO_AI_FLOW] Failed to get orchestration plan: {e}")
            orchestration_result = {
                "error": "Failed to get orchestration plan",
                "details": str(e)
            }
        
        # Get analysis summary from current session
        analysis_summary = None
        if self.current_analysis_session:
            result = self.current_analysis_session["analysis_result"]
            analysis_summary = {
                "final_completeness_score": result.get("final_completeness_score"),
                "iterations_used": result.get("iterations_used"),
                "deliverables": result.get("deliverables"),
                "executive_summary": result.get("executive_summary")
            }
        
        # Create result structure
        result = {
            "polished_prompt": polished_prompt,
            "analysis_summary": analysis_summary,
            "orchestration_result": orchestration_result,
            "success": orchestration_result is not None and "error" not in orchestration_result,
            "ready_for_execution": orchestration_result is not None and "steps" in orchestration_result
        }
        
        self.logger.info(f"[CEO_AI_FLOW] Finalization complete")
        
        return result
    
    def reset_session(self):
        """Reset the conversation session"""
        self.current_analysis_session = None
        self.logger.info("[CEO_AI_FLOW] Session reset")
    
    def get_analysis_summary(self) -> Optional[Dict[str, Any]]:
        """Get summary of current AI analysis"""
        if not self.current_analysis_session:
            return None
        
        result = self.current_analysis_session["analysis_result"]
        return {
            "state": result.get("state"),
            "completeness_score": result.get("completeness_score") or result.get("final_completeness_score"),
            "iterations": result.get("iteration") or result.get("iterations_used"),
            "requires_input": result.get("requires_user_input", False)
        }


    def get_initial_questions(self, task: str) -> List[Dict[str, Any]]:
        """Get initial questions based on task analysis"""
        # Return empty list as this is handled by AI task analyzer
        return []
    
    def generate_requirements_summary(self, responses: Dict[str, Any]) -> Dict[str, Any]:
        """Generate requirements summary from collected responses"""
        # Create a basic summary structure from responses
        summary = {
            "purpose": responses.get("purpose", "Not specified"),
            "target_audience": responses.get("audience", "General users"),
            "scope": {
                "included": responses.get("scope", "To be determined")
            },
            "timeline": responses.get("timeline", "Flexible"),
            "constraints": responses.get("constraints", "No specific constraints"),
            "priority": "normal",
            "success_criteria": ["Task completed successfully"]
        }
        
        return summary


# Export the conversation flow manager
ceo_conversation_flow = CEOConversationFlow()
