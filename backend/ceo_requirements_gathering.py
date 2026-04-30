from fastapi import APIRouter, HTTPException, Request
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
import logging
import json

from models import (
    CEORequirementsRequest,
    CEORequirementsResponse,
    CEOClarificationRequest,
    CEOClarificationResponse,
    CEORequirementAnalysis,
    CEOPolishedRequirement,
    CEORequirementLearning
)
from ai_service import ai_service
from logging_config import log_orchestration_event
from exceptions import TaskValidationException
from ceo_conversation_flow import ceo_conversation_flow, ConversationState

# Create CEO requirements gathering router
ceo_requirements_router = APIRouter(prefix="/api/ceo/requirements")

# Initialize logger
logger = logging.getLogger(__name__)

# In-memory storage for requirements gathering sessions
requirements_sessions = {}
requirements_learning_matrix = []


class CEORequirementsGatherer:
    """CEO Requirements Gathering Agent with Learning Capabilities"""
    
    def __init__(self):
        self.learning_matrix = []
        self.conversation_flow = ceo_conversation_flow
        self.active_sessions = {}  # Track active conversation sessions
        self.clarification_patterns = {
            "purpose": [
                "What is the main purpose of this task?",
                "What business goal are you trying to achieve?",
                "What problem are you trying to solve?"
            ],
            "target_audience": [
                "Who is the target audience for this?",
                "Who will be using or consuming the output?",
                "What demographic should we focus on?"
            ],
            "scope": [
                "What is the scope of this project?",
                "Are there any specific requirements or constraints?",
                "What should be included or excluded?"
            ],
            "timeline": [
                "When do you need this completed?",
                "Is there a specific deadline?",
                "What is the urgency level?"
            ],
            "format": [
                "What format do you prefer for the output?",
                "How should the final deliverable be structured?",
                "Are there any specific formatting requirements?"
            ],
            "tone": [
                "What tone should be used?",
                "Should this be formal or casual?",
                "What style would best fit your needs?"
            ]
        }
    
    async def analyze_initial_task(self, task: str, request_id: str) -> Dict[str, Any]:
        """Analyze initial task and determine what clarifications are needed."""
        
        analysis_prompt = f"""
As a CEO, I need to analyze this task request and determine what additional information is needed to create clear, actionable requirements.

Task: {task}

Analyze the task and identify missing information in these categories:
1. Purpose/Goal - Is the business objective clear?
2. Target Audience - Is the intended audience specified?
3. Scope - Are the boundaries and requirements clear?
4. Timeline - Is there a deadline or urgency?
5. Format - Is the desired output format specified?
6. Tone/Style - Is the communication style clear?
7. Context - Is there sufficient background information?

For each missing category, rate the importance (1-5) and suggest specific questions to ask.

Return your analysis in this JSON format:
{{
    "completeness_score": <1-10>,
    "missing_categories": [
        {{
            "category": "purpose",
            "importance": 5,
            "questions": ["What is the main business goal?"],
            "reason": "Purpose is unclear"
        }}
    ],
    "clarity_issues": ["List any unclear aspects"],
    "ready_to_proceed": false,
    "next_action": "clarification_needed"
}}
"""
        
        try:
            analysis_result = await ai_service.generate_content(analysis_prompt, request_id)
            
            # Parse JSON response
            try:
                analysis_data = json.loads(analysis_result)
            except json.JSONDecodeError:
                # If JSON parsing fails, extract key information and create structured response
                logger.warning(f"CEO analysis JSON parsing failed, creating fallback analysis for request {request_id}")
                analysis_data = self._create_fallback_analysis(task, analysis_result)
            
            # Ensure required fields exist
            analysis_data = self._validate_and_fix_analysis(analysis_data)
            
            log_orchestration_event(
                request_id=request_id,
                event_type="ceo_requirements_analysis",
                message=f"CEO analyzed task completeness: {analysis_data.get('completeness_score', 0)}/10",
                additional_data={
                    "completeness_score": analysis_data.get("completeness_score", 0),
                    "missing_categories_count": len(analysis_data.get("missing_categories", [])),
                    "ready_to_proceed": analysis_data.get("ready_to_proceed", False)
                }
            )
            
            return analysis_data
            
        except Exception as e:
            logger.error(f"CEO requirements analysis failed: {e}")
            # Return a working fallback analysis instead of raising exception
            return self._create_emergency_fallback_analysis(task)
    
    def _create_fallback_analysis(self, task: str, ai_response: str) -> Dict[str, Any]:
        """Create fallback analysis when JSON parsing fails but AI responded"""
        # Analyze task length and content to determine completeness
        task_words = task.split()
        completeness_score = min(8, max(3, len(task_words) // 2))  # 3-8 based on task length
        
        # Generate basic questions based on task content
        missing_categories = []
        
        if "purpose" not in task.lower() and "goal" not in task.lower():
            missing_categories.append({
                "category": "purpose",
                "importance": 5,
                "questions": ["What is the main purpose or goal of this task?"],
                "reason": "Business objective needs clarification"
            })
        
        if "audience" not in task.lower() and "user" not in task.lower():
            missing_categories.append({
                "category": "target_audience",
                "importance": 4,
                "questions": ["Who is the target audience for this?"],
                "reason": "Target audience not specified"
            })
        
        if len(task_words) < 10:  # Short task likely needs more detail
            missing_categories.append({
                "category": "scope",
                "importance": 4,
                "questions": ["Can you provide more details about the scope and requirements?"],
                "reason": "Task description needs more detail"
            })
        
        return {
            "completeness_score": completeness_score,
            "missing_categories": missing_categories,
            "clarity_issues": ["Some aspects need clarification"],
            "ready_to_proceed": len(missing_categories) == 0 and completeness_score >= 7,
            "next_action": "clarification_needed" if missing_categories else "proceed"
        }
    
    def _create_emergency_fallback_analysis(self, task: str) -> Dict[str, Any]:
        """Create emergency fallback when everything fails"""
        return {
            "completeness_score": 4,
            "missing_categories": [
                {
                    "category": "general",
                    "importance": 4,
                    "questions": [
                        "What is the main goal of this task?",
                        "Who is your target audience?",
                        "What format would you like for the output?"
                    ],
                    "reason": "Need more information to proceed effectively"
                }
            ],
            "clarity_issues": ["Task needs more detail for optimal results"],
            "ready_to_proceed": False,
            "next_action": "clarification_needed"
        }
    
    def _validate_and_fix_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix analysis data structure"""
        # Ensure all required fields exist with defaults
        defaults = {
            "completeness_score": 5,
            "missing_categories": [],
            "clarity_issues": [],
            "ready_to_proceed": False,
            "next_action": "clarification_needed"
        }
        
        for key, default_value in defaults.items():
            if key not in analysis_data:
                analysis_data[key] = default_value
        
        # Validate completeness_score is in range
        if not isinstance(analysis_data["completeness_score"], int) or analysis_data["completeness_score"] < 1:
            analysis_data["completeness_score"] = 5
        elif analysis_data["completeness_score"] > 10:
            analysis_data["completeness_score"] = 10
        
        # Ensure missing_categories is a list
        if not isinstance(analysis_data["missing_categories"], list):
            analysis_data["missing_categories"] = []
        
        # Validate each category has required fields
        for category in analysis_data["missing_categories"]:
            if "questions" not in category or not category["questions"]:
                category["questions"] = ["Can you provide more details about this aspect?"]
        
        return analysis_data
    
    async def generate_clarification_questions(self, missing_categories: List[Dict], task: str, request_id: str, strategy: str = "adaptive") -> List[Dict[str, Any]]:
        """Generate specific clarification questions based on missing categories using conversation flow."""
        
        # Use conversation flow to generate questions
        question_objects = self.conversation_flow.get_initial_questions(task, strategy)
        
        # If conversation flow doesn't generate enough questions, fall back to original logic
        if len(question_objects) < 3:
            questions = []
            
            # Ensure we have categories to work with
            if not missing_categories:
                # Generate default questions if no categories provided
                questions = [
                    "What is the main goal of this task?",
                    "Who is your target audience?",
                    "What format would you prefer for the output?"
                ]
            else:
                # Sort by importance (highest first)
                sorted_categories = sorted(missing_categories, key=lambda x: x.get('importance', 0), reverse=True)
                
                # Limit to top 3-5 most important questions to avoid overwhelming user
                for category in sorted_categories[:5]:
                    category_name = category.get('category', '')
                    category_questions = category.get('questions', [])
                    
                    if category_questions:
                        # Use questions from the analysis
                        questions.extend(category_questions)
                    elif category_name in self.clarification_patterns:
                        # Use predefined patterns
                        pattern_questions = self.clarification_patterns[category_name]
                        questions.extend(pattern_questions[:1])  # Take first question from pattern
                    else:
                        # Generate a generic question for unknown categories
                        questions.append(f"Can you provide more details about the {category_name}?")
            
            # If we still don't have enough questions, generate more using AI
            if len(questions) < 2:
                try:
                    context_prompt = f"""
Based on this task: "{task}"

Generate 3 specific clarification questions that would help create better requirements. Focus on:
- Understanding the business context
- Clarifying success criteria  
- Identifying constraints or preferences

Return only the questions, one per line:
"""
                    
                    additional_questions_response = await ai_service.generate_content(context_prompt, request_id)
                    additional_questions = [q.strip() for q in additional_questions_response.split('\n') if q.strip() and '?' in q]
                    questions.extend(additional_questions)
                    
                except Exception as e:
                    logger.warning(f"Failed to generate additional questions: {e}")
                    # Add fallback questions if AI fails
                    fallback_questions = [
                        "What specific outcome are you looking for?",
                        "Are there any constraints or requirements I should know about?",
                        "When do you need this completed?"
                    ]
                    questions.extend(fallback_questions)
            
            # Remove duplicates and limit to 5 questions
            unique_questions = list(dict.fromkeys(questions))[:5]
            
            # Convert to question objects format
            question_objects = [
                {
                    "id": f"q_{i+1}",
                    "question": q,
                    "area": "general",
                    "type": "primary",
                    "required": i < 2  # First 2 questions are required
                }
                for i, q in enumerate(unique_questions)
            ]
        
        # Ensure we always have at least one question
        if not question_objects:
            question_objects = [{
                "id": "q_default",
                "question": "Can you provide more details about what you're trying to achieve?",
                "area": "general",
                "type": "primary",
                "required": True
            }]
        
        log_orchestration_event(
            request_id=request_id,
            event_type="ceo_clarification_questions_generated",
            message=f"CEO generated {len(question_objects)} clarification questions using {strategy} strategy",
            additional_data={
                "questions_count": len(question_objects),
                "strategy": strategy,
                "categories_addressed": [cat.get('category', 'unknown') for cat in missing_categories[:5]] if missing_categories else ["default"]
            }
        )
        
        return question_objects
    
    async def polish_requirements(self, original_task: str, clarifications: Dict[str, str], request_id: str) -> Dict[str, Any]:
        """Polish the original task into clear requirements based on clarifications."""
        
        clarification_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in clarifications.items()])
        
        polish_prompt = f"""
As a CEO, I need to transform this initial task into a clear, actionable requirement document.

Original Task: {original_task}

Clarifications Provided:
{clarification_text}

Create a polished requirement that includes:
1. Clear objective and purpose
2. Target audience and context
3. Specific deliverables
4. Success criteria
5. Constraints and preferences
6. Timeline (if provided)

Return the polished requirement in this JSON format:
{{
    "polished_task": "Clear, actionable task description",
    "objective": "Main business objective",
    "target_audience": "Intended audience",
    "deliverables": ["List of specific deliverables"],
    "success_criteria": ["How to measure success"],
    "constraints": ["Any limitations or requirements"],
    "timeline": "Timeline information",
    "additional_context": "Any other relevant information",
    "agent_plan_suggestion": "Suggested agents to use for this task"
}}
"""
        
        try:
            polished_result = await ai_service.generate_content(polish_prompt, request_id)
            polished_data = json.loads(polished_result)
            
            # Store learning for future similar requests
            learning_entry = {
                "original_task": original_task,
                "clarifications": clarifications,
                "polished_requirement": polished_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": request_id
            }
            
            self.learning_matrix.append(learning_entry)
            requirements_learning_matrix.append(learning_entry)
            
            log_orchestration_event(
                request_id=request_id,
                event_type="ceo_requirements_polished",
                message="CEO successfully polished requirements",
                additional_data={
                    "original_task_length": len(original_task),
                    "polished_task_length": len(polished_data.get("polished_task", "")),
                    "clarifications_count": len(clarifications),
                    "deliverables_count": len(polished_data.get("deliverables", [])),
                    "learning_entries_total": len(self.learning_matrix)
                }
            )
            
            return polished_data
            
        except json.JSONDecodeError:
            logger.warning(f"CEO requirements polishing JSON parsing failed for request {request_id}")
            # Fallback polished requirement
            return {
                "polished_task": f"{original_task}\n\nBased on clarifications: {clarification_text}",
                "objective": "Complete the requested task with provided clarifications",
                "target_audience": "General audience",
                "deliverables": ["Task completion"],
                "success_criteria": ["Task completed successfully"],
                "constraints": [],
                "timeline": "As soon as possible",
                "additional_context": clarification_text,
                "agent_plan_suggestion": "Use appropriate agents based on task type"
            }
        except Exception as e:
            logger.error(f"CEO requirements polishing failed: {e}")
            raise Exception(f"Requirements polishing failed: {str(e)}")
    
    def find_similar_requirements(self, task: str, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Find similar requirements from learning matrix for pattern reuse."""
        
        similar_requirements = []
        task_lower = task.lower()
        
        for entry in self.learning_matrix:
            original_task_lower = entry["original_task"].lower()
            
            # Simple similarity check (can be enhanced with embeddings)
            common_words = set(task_lower.split()) & set(original_task_lower.split())
            similarity = len(common_words) / max(len(task_lower.split()), len(original_task_lower.split()))
            
            if similarity >= threshold:
                similar_requirements.append({
                    "similarity": similarity,
                    "entry": entry
                })
        
        # Sort by similarity (highest first)
        similar_requirements.sort(key=lambda x: x["similarity"], reverse=True)
        
        return similar_requirements[:3]  # Return top 3 similar requirements
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights about requirements gathering patterns."""
        
        if not self.learning_matrix:
            return {
                "total_requirements": 0,
                "common_clarifications": [],
                "frequent_patterns": [],
                "insights": "No learning data available yet"
            }
        
        # Analyze common clarification patterns
        all_clarifications = []
        for entry in self.learning_matrix:
            all_clarifications.extend(entry["clarifications"].keys())
        
        from collections import Counter
        clarification_counts = Counter(all_clarifications)
        
        return {
            "total_requirements": len(self.learning_matrix),
            "common_clarifications": clarification_counts.most_common(5),
            "frequent_patterns": self._analyze_patterns(),
            "insights": f"Processed {len(self.learning_matrix)} requirements. Most common clarifications focus on purpose and audience."
        }
    
    def _analyze_patterns(self) -> List[Dict[str, Any]]:
        """Analyze patterns in requirements gathering."""
        
        patterns = []
        
        # Analyze task types
        task_types = {}
        for entry in self.learning_matrix:
            task = entry["original_task"].lower()
            if "blog" in task or "article" in task or "content" in task:
                task_types["content_creation"] = task_types.get("content_creation", 0) + 1
            elif "social media" in task or "post" in task:
                task_types["social_media"] = task_types.get("social_media", 0) + 1
            elif "marketing" in task or "campaign" in task:
                task_types["marketing"] = task_types.get("marketing", 0) + 1
            else:
                task_types["general"] = task_types.get("general", 0) + 1
        
        for task_type, count in task_types.items():
            patterns.append({
                "pattern_type": "task_category",
                "pattern": task_type,
                "frequency": count,
                "percentage": round((count / len(self.learning_matrix)) * 100, 1)
            })
        
        return patterns


# Initialize CEO Requirements Gatherer
ceo_requirements_gatherer = CEORequirementsGatherer()


@ceo_requirements_router.post("/start", response_model=CEORequirementsResponse)
async def start_requirements_gathering(req: CEORequirementsRequest, request: Request):
    """Start the requirements gathering process with CEO agent."""
    
    task = req.task.strip()
    if not task:
        raise TaskValidationException("Task cannot be empty")
    
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    session_id = str(uuid.uuid4())
    
    log_orchestration_event(
        request_id=request_id,
        event_type="ceo_requirements_start",
        message=f"CEO starting requirements gathering for task: {task[:100]}{'...' if len(task) > 100 else ''}",
        additional_data={
            "session_id": session_id,
            "task_length": len(task),
            "user_context": req.user_context
        }
    )
    
    # Check for similar requirements from learning matrix
    similar_requirements = ceo_requirements_gatherer.find_similar_requirements(task)
    
    # Analyze the task to determine what clarifications are needed
    analysis = await ceo_requirements_gatherer.analyze_initial_task(task, request_id)
    
    # Store session data
    requirements_sessions[session_id] = {
        "request_id": request_id,
        "original_task": task,
        "user_context": req.user_context,
        "analysis": analysis,
        "clarifications": {},
        "similar_requirements": similar_requirements,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "gathering_requirements"
    }
    
    # If task is complete enough, proceed directly
    if analysis.get("ready_to_proceed", False) and analysis.get("completeness_score", 0) >= 8:
        # Task is clear enough, proceed with polishing
        polished = await ceo_requirements_gatherer.polish_requirements(task, {}, request_id)
        
        requirements_sessions[session_id]["status"] = "requirements_complete"
        requirements_sessions[session_id]["polished_requirement"] = polished
        
        return CEORequirementsResponse(
            session_id=session_id,
            request_id=request_id,
            status="requirements_complete",
            message="Task is clear enough to proceed. Requirements have been polished.",
            analysis=CEORequirementAnalysis(**analysis),
            clarification_questions=[],
            polished_requirement=CEOPolishedRequirement(**polished),
            similar_requirements=similar_requirements,
            next_action="proceed_to_orchestration",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    # Generate clarification questions using conversation flow
    question_objects = await ceo_requirements_gatherer.generate_clarification_questions(
        analysis.get("missing_categories", []), task, request_id
    )
    
    # Convert question objects to list of strings for backward compatibility
    questions = [q["question"] for q in question_objects]
    
    return CEORequirementsResponse(
        session_id=session_id,
        request_id=request_id,
        status="awaiting_clarification",
        message=f"I need some clarification to create the best possible plan. Please answer {len(questions)} questions.",
        analysis=CEORequirementAnalysis(**analysis),
        clarification_questions=questions,
        similar_requirements=similar_requirements,
        next_action="provide_clarifications",
        timestamp=datetime.now(timezone.utc).isoformat()
    )


@ceo_requirements_router.post("/clarify", response_model=CEORequirementsResponse)
async def provide_clarifications(req: CEOClarificationRequest, request: Request):
    """Provide clarifications to CEO agent questions."""
    
    session_id = req.session_id
    if session_id not in requirements_sessions:
        raise HTTPException(status_code=404, detail="Requirements session not found")
    
    session = requirements_sessions[session_id]
    request_id = session["request_id"]
    
    # Update clarifications
    session["clarifications"].update(req.clarifications)
    
    log_orchestration_event(
        request_id=request_id,
        event_type="ceo_clarifications_received",
        message=f"CEO received {len(req.clarifications)} clarifications",
        additional_data={
            "session_id": session_id,
            "clarifications_count": len(req.clarifications),
            "total_clarifications": len(session["clarifications"])
        }
    )
    
    # Analyze if we have enough information now
    clarification_text = " ".join(req.clarifications.values())
    combined_context = f"{session['original_task']} {clarification_text}"
    
    # Re-analyze with clarifications
    updated_analysis = await ceo_requirements_gatherer.analyze_initial_task(combined_context, request_id)
    session["analysis"] = updated_analysis
    
    # If we have enough information, polish requirements
    if (updated_analysis.get("ready_to_proceed", False) or 
        updated_analysis.get("completeness_score", 0) >= 7 or 
        len(session["clarifications"]) >= 5):  # Max 5 rounds of clarification
        
        # Polish the requirements
        polished = await ceo_requirements_gatherer.polish_requirements(
            session["original_task"], 
            session["clarifications"], 
            request_id
        )
        
        session["status"] = "requirements_complete"
        session["polished_requirement"] = polished
        
        return CEORequirementsResponse(
            session_id=session_id,
            request_id=request_id,
            status="requirements_complete",
            message="Perfect! I have all the information needed. Here are your polished requirements.",
            analysis=CEORequirementAnalysis(**updated_analysis),
            clarification_questions=[],
            polished_requirement=CEOPolishedRequirement(**polished),
            similar_requirements=session.get("similar_requirements", []),
            next_action="proceed_to_orchestration",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    # Need more clarifications
    remaining_questions = await ceo_requirements_gatherer.generate_clarification_questions(
        updated_analysis.get("missing_categories", []), 
        combined_context, 
        request_id
    )
    
    return CEORequirementsResponse(
        session_id=session_id,
        request_id=request_id,
        status="awaiting_clarification",
        message=f"Thank you for the clarifications! I need just a bit more information ({len(remaining_questions)} more questions).",
        analysis=CEORequirementAnalysis(**updated_analysis),
        clarification_questions=remaining_questions,
        similar_requirements=session.get("similar_requirements", []),
        next_action="provide_clarifications",
        timestamp=datetime.now(timezone.utc).isoformat()
    )


@ceo_requirements_router.post("/orchestrate/{session_id}")
async def proceed_to_orchestration(session_id: str, request: Request):
    """Proceed to orchestration with polished requirements."""
    
    if session_id not in requirements_sessions:
        raise HTTPException(status_code=404, detail="Requirements session not found")
    
    session = requirements_sessions[session_id]
    
    if session["status"] != "requirements_complete":
        raise HTTPException(status_code=400, detail="Requirements not yet complete")
    
    polished_requirement = session["polished_requirement"]
    request_id = session["request_id"]
    
    log_orchestration_event(
        request_id=request_id,
        event_type="ceo_orchestration_handoff",
        message="CEO handing off polished requirements to orchestration",
        additional_data={
            "session_id": session_id,
            "polished_task": polished_requirement["polished_task"][:100] + "...",
            "suggested_agents": polished_requirement.get("agent_plan_suggestion", "")
        }
    )
    
    # Call the orchestration endpoint with polished requirements
    import httpx
    
    orchestration_payload = {
        "task": polished_requirement["polished_task"],
        "context": f"Objective: {polished_requirement['objective']}\nTarget Audience: {polished_requirement['target_audience']}\nDeliverables: {', '.join(polished_requirement.get('deliverables', []))}\nSuccess Criteria: {', '.join(polished_requirement.get('success_criteria', []))}",
        "metadata": {
            "requirements_session_id": session_id,
            "original_task": session["original_task"],
            "clarifications_provided": len(session["clarifications"]),
            "polished_by_ceo": True
        }
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/ceo/orchestrate",
                json=orchestration_payload
            )
            response.raise_for_status()
            
            orchestration_result = response.json()
            
            # Update session with orchestration result
            session["orchestration_result"] = orchestration_result
            session["status"] = "orchestration_complete"
            
            return {
                "status": "success",
                "message": "Requirements gathered and orchestration completed successfully",
                "session_id": session_id,
                "polished_requirement": polished_requirement,
                "orchestration_result": orchestration_result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except httpx.HTTPError as e:
            logger.error(f"Orchestration call failed: {e}")
            raise HTTPException(status_code=500, detail=f"Orchestration failed: {str(e)}")
        except Exception as e:
            logger.error(f"Orchestration error: {e}")
            raise HTTPException(status_code=500, detail=f"Orchestration error: {str(e)}")


@ceo_requirements_router.get("/session/{session_id}")
async def get_requirements_session(session_id: str):
    """Get requirements gathering session details."""
    
    if session_id not in requirements_sessions:
        raise HTTPException(status_code=404, detail="Requirements session not found")
    
    return {
        "status": "success",
        "session": requirements_sessions[session_id],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@ceo_requirements_router.get("/learning/insights")
async def get_requirements_learning_insights():
    """Get insights about requirements gathering learning patterns."""
    
    insights = ceo_requirements_gatherer.get_learning_insights()
    
    return {
        "status": "success",
        "learning_insights": insights,
        "total_sessions": len(requirements_sessions),
        "learning_matrix_size": len(requirements_learning_matrix),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@ceo_requirements_router.get("/learning/matrix")
async def get_requirements_learning_matrix():
    """Get the complete requirements learning matrix."""
    
    return {
        "status": "success",
        "learning_matrix": requirements_learning_matrix,
        "total_entries": len(requirements_learning_matrix),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# Export router
__all__ = ["ceo_requirements_router", "ceo_requirements_gatherer", "CEORequirementsGatherer"]
