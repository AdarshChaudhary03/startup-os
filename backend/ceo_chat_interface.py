from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
import logging
import json
import asyncio

from models import (
    CEORequirementsRequest,
    CEORequirementsResponse,
    CEOClarificationRequest
)
from ceo_requirements_gathering import ceo_requirements_gatherer, requirements_sessions
from ai_service import ai_service
from logging_config import log_orchestration_event
from exceptions import TaskValidationException

# Create CEO chat interface router
ceo_chat_router = APIRouter(prefix="/api/ceo/chat")

# Initialize logger
logger = logging.getLogger(__name__)

# Active WebSocket connections for real-time chat
active_connections: Dict[str, WebSocket] = {}
chat_sessions: Dict[str, Dict[str, Any]] = {}


class CEOChatManager:
    """CEO Chat Manager for real-time conversation with users"""
    
    def __init__(self):
        self.conversation_templates = {
            "greeting": [
                "Hello! I'm your CEO agent. I'm here to help you create clear, actionable requirements for your task.",
                "Let's work together to understand exactly what you need so I can orchestrate the best team for the job.",
                "What would you like to accomplish today?"
            ],
            "clarification_intro": [
                "I need to understand your requirements better to ensure we deliver exactly what you need.",
                "Let me ask you a few questions to clarify the details.",
                "This will help me create the perfect plan and choose the right team members."
            ],
            "requirements_complete": [
                "Excellent! I now have all the information I need.",
                "Let me polish your requirements and create an execution plan.",
                "I'll orchestrate the best team to deliver your project."
            ],
            "error_recovery": [
                "I apologize for the confusion. Let me try a different approach.",
                "Let's simplify this. Can you tell me in your own words what you're trying to achieve?",
                "I'm here to help. What's the main goal of your project?"
            ]
        }
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept WebSocket connection and initialize chat session"""
        await websocket.accept()
        active_connections[session_id] = websocket
        
        # Initialize chat session
        chat_sessions[session_id] = {
            "session_id": session_id,
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "conversation_history": [],
            "current_state": "greeting",
            "requirements_session_id": None,
            "user_context": {},
            "clarification_count": 0
        }
        
        # Send greeting message
        await self.send_ceo_message(session_id, {
            "type": "greeting",
            "message": "\n".join(self.conversation_templates["greeting"]),
            "suggestions": [
                "I need help with content creation",
                "I want to launch a marketing campaign", 
                "I need to create social media content",
                "I have a specific project in mind"
            ]
        })
        
        logger.info(f"CEO chat session {session_id} connected")
    
    def disconnect(self, session_id: str):
        """Handle WebSocket disconnection"""
        if session_id in active_connections:
            del active_connections[session_id]
        
        if session_id in chat_sessions:
            chat_sessions[session_id]["disconnected_at"] = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"CEO chat session {session_id} disconnected")
    
    async def send_ceo_message(self, session_id: str, message_data: Dict[str, Any]):
        """Send message from CEO to user"""
        if session_id not in active_connections:
            return
        
        websocket = active_connections[session_id]
        
        # Add metadata
        message_data.update({
            "from": "ceo",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id
        })
        
        # Store in conversation history
        if session_id in chat_sessions:
            chat_sessions[session_id]["conversation_history"].append(message_data)
        
        try:
            await websocket.send_text(json.dumps(message_data))
        except Exception as e:
            logger.error(f"Error sending message to {session_id}: {e}")
            self.disconnect(session_id)
    
    async def handle_user_message(self, session_id: str, message: str):
        """Handle incoming message from user"""
        if session_id not in chat_sessions:
            await self.send_ceo_message(session_id, {
                "type": "error",
                "message": "Session not found. Please refresh and try again."
            })
            return
        
        session = chat_sessions[session_id]
        
        # Store user message in conversation history
        user_message_data = {
            "from": "user",
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        session["conversation_history"].append(user_message_data)
        
        # Process message based on current state
        current_state = session["current_state"]
        
        try:
            if current_state == "greeting":
                await self._handle_initial_task(session_id, message)
            elif current_state == "clarification":
                await self._handle_clarification_response(session_id, message)
            elif current_state == "requirements_review":
                await self._handle_requirements_review(session_id, message)
            else:
                await self._handle_general_conversation(session_id, message)
        
        except Exception as e:
            logger.error(f"Error handling user message in session {session_id}: {e}")
            await self.send_ceo_message(session_id, {
                "type": "error",
                "message": "I encountered an error processing your request. Let me try again.",
                "suggestions": ["Can you rephrase your request?", "Let's start over"]
            })
    
    async def _handle_initial_task(self, session_id: str, task: str):
        """Handle initial task submission from user"""
        session = chat_sessions[session_id]
        
        # Send thinking message
        await self.send_ceo_message(session_id, {
            "type": "thinking",
            "message": "Let me analyze your task and determine what information I need..."
        })
        
        try:
            # Start requirements gathering process
            from ceo_requirements_gathering import ceo_requirements_router
            
            # Create requirements request
            req = CEORequirementsRequest(
                task=task,
                user_context=session.get("user_context", {})
            )
            
            # Mock request object for requirements gathering
            class MockRequest:
                def __init__(self, session_id):
                    self.state = type('State', (), {'request_id': session_id})()
            
            mock_request = MockRequest(session_id)
            
            # Call requirements gathering
            requirements_response = await ceo_requirements_gatherer.analyze_initial_task(task, session_id)
            
            # Store requirements session ID
            requirements_session_id = str(uuid.uuid4())
            session["requirements_session_id"] = requirements_session_id
            
            # Check if clarification is needed
            if requirements_response.get("ready_to_proceed", False):
                # Task is clear enough
                session["current_state"] = "requirements_complete"
                
                await self.send_ceo_message(session_id, {
                    "type": "requirements_complete",
                    "message": "Perfect! Your task is clear and I have all the information I need.",
                    "analysis": requirements_response,
                    "actions": ["Proceed to create execution plan", "Review requirements"]
                })
                
                # Automatically proceed to orchestration
                await self._proceed_to_orchestration(session_id, task)
            
            else:
                # Need clarification
                session["current_state"] = "clarification"
                session["pending_questions"] = []
                
                # Generate clarification questions
                questions = await ceo_requirements_gatherer.generate_clarification_questions(
                    requirements_response.get("missing_categories", []), task, session_id
                )
                
                session["pending_questions"] = questions
                session["current_question_index"] = 0
                
                # Send first clarification question
                await self._ask_next_clarification_question(session_id)
        
        except Exception as e:
            logger.error(f"Error in initial task handling: {e}")
            await self.send_ceo_message(session_id, {
                "type": "error",
                "message": "I had trouble analyzing your task. Let me ask you directly:",
                "questions": ["What is the main goal of your project?", "Who is your target audience?"]
            })
    
    async def _ask_next_clarification_question(self, session_id: str):
        """Ask the next clarification question"""
        session = chat_sessions[session_id]
        
        if "pending_questions" not in session or not session["pending_questions"]:
            await self._complete_requirements_gathering(session_id)
            return
        
        current_index = session.get("current_question_index", 0)
        questions = session["pending_questions"]
        
        if current_index >= len(questions):
            await self._complete_requirements_gathering(session_id)
            return
        
        question = questions[current_index]
        remaining_questions = len(questions) - current_index
        
        await self.send_ceo_message(session_id, {
            "type": "clarification_question",
            "message": question,
            "context": f"Question {current_index + 1} of {len(questions)}",
            "progress": {
                "current": current_index + 1,
                "total": len(questions),
                "remaining": remaining_questions - 1
            },
            "suggestions": self._get_question_suggestions(question)
        })
    
    def _get_question_suggestions(self, question: str) -> List[str]:
        """Get contextual suggestions for a question"""
        question_lower = question.lower()
        
        if "purpose" in question_lower or "goal" in question_lower:
            return ["Increase brand awareness", "Generate leads", "Educate audience", "Drive sales"]
        elif "audience" in question_lower or "target" in question_lower:
            return ["Business professionals", "Young adults (18-35)", "General public", "Industry experts"]
        elif "format" in question_lower or "output" in question_lower:
            return ["Blog post", "Social media posts", "Email campaign", "Video content"]
        elif "timeline" in question_lower or "deadline" in question_lower:
            return ["ASAP", "Within a week", "Within a month", "No specific deadline"]
        else:
            return ["Yes", "No", "Not sure", "Let me think about it"]
    
    async def _handle_clarification_response(self, session_id: str, response: str):
        """Handle user's response to clarification question"""
        session = chat_sessions[session_id]
        
        # Store the response
        if "clarification_responses" not in session:
            session["clarification_responses"] = {}
        
        current_index = session.get("current_question_index", 0)
        questions = session.get("pending_questions", [])
        
        if current_index < len(questions):
            question = questions[current_index]
            session["clarification_responses"][question] = response
            session["clarification_count"] += 1
        
        # Send acknowledgment
        await self.send_ceo_message(session_id, {
            "type": "acknowledgment",
            "message": "Thank you for that information!"
        })
        
        # Move to next question
        session["current_question_index"] = current_index + 1
        
        # Small delay for natural conversation flow
        await asyncio.sleep(1)
        
        await self._ask_next_clarification_question(session_id)
    
    async def _complete_requirements_gathering(self, session_id: str):
        """Complete the requirements gathering process"""
        session = chat_sessions[session_id]
        
        await self.send_ceo_message(session_id, {
            "type": "processing",
            "message": "Excellent! Let me process all your responses and create polished requirements..."
        })
        
        try:
            # Get original task from conversation history
            original_task = ""
            for msg in session["conversation_history"]:
                if msg.get("from") == "user" and len(msg.get("message", "")) > 10:
                    original_task = msg["message"]
                    break
            
            clarifications = session.get("clarification_responses", {})
            
            # Polish requirements
            polished = await ceo_requirements_gatherer.polish_requirements(
                original_task, clarifications, session_id
            )
            
            session["polished_requirements"] = polished
            session["current_state"] = "requirements_complete"
            
            await self.send_ceo_message(session_id, {
                "type": "requirements_complete",
                "message": "\n".join(self.conversation_templates["requirements_complete"]),
                "polished_requirements": polished,
                "actions": ["Proceed with execution", "Review requirements", "Make changes"]
            })
            
            # Automatically proceed to orchestration after a brief pause
            await asyncio.sleep(2)
            await self._proceed_to_orchestration(session_id, polished["polished_task"])
        
        except Exception as e:
            logger.error(f"Error completing requirements gathering: {e}")
            await self.send_ceo_message(session_id, {
                "type": "error",
                "message": "I had trouble processing your requirements. Let me try a simpler approach.",
                "fallback_action": "proceed_with_original_task"
            })
    
    async def _proceed_to_orchestration(self, session_id: str, task: str):
        """Proceed to orchestration with polished requirements"""
        session = chat_sessions[session_id]
        
        await self.send_ceo_message(session_id, {
            "type": "orchestration_start",
            "message": "Now I'm creating your execution plan and assembling the perfect team..."
        })
        
        try:
            # Call orchestration endpoint
            import httpx
            
            orchestration_payload = {
                "task": task,
                "metadata": {
                    "chat_session_id": session_id,
                    "requirements_gathered": True,
                    "clarifications_count": session.get("clarification_count", 0)
                }
            }
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "http://localhost:8000/api/ceo/orchestrate",
                    json=orchestration_payload
                )
                response.raise_for_status()
                
                orchestration_result = response.json()
                
                session["orchestration_result"] = orchestration_result
                session["current_state"] = "orchestration_complete"
                
                await self.send_ceo_message(session_id, {
                    "type": "orchestration_complete",
                    "message": "Perfect! Your project has been completed successfully.",
                    "result": orchestration_result,
                    "summary": orchestration_result.get("final_output", ""),
                    "actions": ["View detailed results", "Start new project", "Provide feedback"]
                })
        
        except Exception as e:
            logger.error(f"Error in orchestration: {e}")
            await self.send_ceo_message(session_id, {
                "type": "orchestration_error",
                "message": "I encountered an issue while executing your project. Let me try again or we can modify the approach.",
                "error_details": str(e),
                "actions": ["Retry execution", "Modify requirements", "Contact support"]
            })
    
    async def _handle_requirements_review(self, session_id: str, message: str):
        """Handle user feedback on requirements review"""
        message_lower = message.lower()
        
        if "proceed" in message_lower or "looks good" in message_lower or "yes" in message_lower:
            session = chat_sessions[session_id]
            polished_task = session.get("polished_requirements", {}).get("polished_task", message)
            await self._proceed_to_orchestration(session_id, polished_task)
        
        elif "change" in message_lower or "modify" in message_lower or "no" in message_lower:
            await self.send_ceo_message(session_id, {
                "type": "modification_request",
                "message": "What would you like to change about the requirements?",
                "suggestions": ["Change target audience", "Modify timeline", "Adjust scope", "Different format"]
            })
        
        else:
            await self._handle_general_conversation(session_id, message)
    
    async def _handle_general_conversation(self, session_id: str, message: str):
        """Handle general conversation and provide helpful responses"""
        
        # Use AI to generate contextual response
        conversation_prompt = f"""
As a CEO agent, respond to this user message in a helpful, professional manner.

User message: {message}

Provide a brief, helpful response that:
1. Acknowledges their message
2. Offers assistance
3. Suggests next steps if appropriate

Keep the response conversational and under 100 words.
"""
        
        try:
            ai_response = await ai_service.generate_content(conversation_prompt, session_id)
            
            await self.send_ceo_message(session_id, {
                "type": "conversation",
                "message": ai_response,
                "suggestions": ["Start new project", "Ask a question", "Get help"]
            })
        
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            await self.send_ceo_message(session_id, {
                "type": "fallback",
                "message": "I understand. How can I help you with your project requirements?",
                "suggestions": ["Start new task", "Ask about capabilities", "Get examples"]
            })


# Initialize CEO Chat Manager
ceo_chat_manager = CEOChatManager()


@ceo_chat_router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time CEO chat"""
    await ceo_chat_manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive message from user
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            user_message = message_data.get("message", "")
            if user_message:
                await ceo_chat_manager.handle_user_message(session_id, user_message)
    
    except WebSocketDisconnect:
        ceo_chat_manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error in session {session_id}: {e}")
        ceo_chat_manager.disconnect(session_id)


@ceo_chat_router.get("/sessions/{session_id}")
async def get_chat_session(session_id: str):
    """Get chat session details"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    return {
        "status": "success",
        "session": chat_sessions[session_id],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@ceo_chat_router.get("/sessions")
async def list_chat_sessions():
    """List all active chat sessions"""
    return {
        "status": "success",
        "active_sessions": len(active_connections),
        "total_sessions": len(chat_sessions),
        "sessions": list(chat_sessions.keys()),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# Export router
__all__ = ["ceo_chat_router", "ceo_chat_manager", "CEOChatManager"]
