"""AI-based Task Analysis Service for CEO Agent

This module implements an AI-driven task analysis system that:
1. Analyzes user tasks and provides completeness scores
2. Uses Groq model to dynamically generate clarifying questions
3. Restructures tasks based on user answers
4. Iteratively refines until completeness score >= 9
5. Produces polished prompts for agent planning
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from enum import Enum
from src.services.ai_service import ai_service
import os


class TaskAnalysisState(Enum):
    """States for the AI-based task analysis flow"""
    INITIAL_ANALYSIS = "initial_analysis"
    GENERATING_QUESTIONS = "generating_questions"
    AWAITING_ANSWERS = "awaiting_answers"
    RESTRUCTURING_TASK = "restructuring_task"
    RE_ANALYZING = "re_analyzing"
    FINALIZING = "finalizing"
    COMPLETE = "complete"


class CEOAITaskAnalyzer:
    """AI-based task analyzer for CEO agent using Groq model"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.groq_model = "llama-3.3-70b-versatile"  # Updated to supported Groq model
        self.max_iterations = 5  # Maximum refinement iterations
        self.target_completeness_score = 6  # Lowered threshold from 9 to 6
        
        # Prompts for different stages
        self.analysis_prompt_template = """
You are an expert task analyst. Analyze the following user task and evaluate its completeness.

Task: {task}

Additional Context (if any): {context}

Evaluate the task based on these criteria:
1. **Clarity**: Is the goal clearly stated?
2. **Scope**: Are the boundaries and deliverables well-defined?
3. **Context**: Is there sufficient background information?
4. **Requirements**: Are technical/functional requirements specified?
5. **Constraints**: Are limitations, timeline, or resources mentioned?
6. **Success Criteria**: Are measurable outcomes defined?
7. **Target Audience**: Is the intended user/stakeholder identified?
8. **Dependencies**: Are external dependencies or integrations mentioned?

Provide your analysis in the following JSON format:
{{
    "completeness_score": <number from 1-10>,
    "analysis": {{
        "clarity": {{
            "score": <1-10>,
            "assessment": "<brief assessment>",
            "missing_elements": ["<what's missing>"]
        }},
        "scope": {{
            "score": <1-10>,
            "assessment": "<brief assessment>",
            "missing_elements": ["<what's missing>"]
        }},
        "context": {{
            "score": <1-10>,
            "assessment": "<brief assessment>",
            "missing_elements": ["<what's missing>"]
        }},
        "requirements": {{
            "score": <1-10>,
            "assessment": "<brief assessment>",
            "missing_elements": ["<what's missing>"]
        }},
        "constraints": {{
            "score": <1-10>,
            "assessment": "<brief assessment>",
            "missing_elements": ["<what's missing>"]
        }},
        "success_criteria": {{
            "score": <1-10>,
            "assessment": "<brief assessment>",
            "missing_elements": ["<what's missing>"]
        }},
        "target_audience": {{
            "score": <1-10>,
            "assessment": "<brief assessment>",
            "missing_elements": ["<what's missing>"]
        }},
        "dependencies": {{
            "score": <1-10>,
            "assessment": "<brief assessment>",
            "missing_elements": ["<what's missing>"]
        }}
    }},
    "overall_assessment": "<comprehensive assessment of the task>",
    "key_missing_information": ["<most critical missing pieces>"]
}}
"""

        self.question_generation_prompt_template = """
Based on the task analysis, generate intelligent questions to gather missing information.

Original Task: {task}

Task Analysis:
{analysis}

Key Missing Information:
{missing_info}

Generate 1 specific, contextual question that will help gather the most critical missing information.
Questions should be:
- Clear and specific
- Contextually relevant to the task
- Designed to elicit detailed responses
- Prioritized by importance

Provide the question in JSON format:
{{
    "questions": [
        {{
            "id": "q1",
            "question": "<question text>",
            "purpose": "<what information this question seeks>",
            "category": "<clarity|scope|context|requirements|constraints|success_criteria|audience|dependencies>",
            "priority": "high"
        }}
    ]
}}
"""

        self.task_restructuring_prompt_template = """
Restructure the task description incorporating the new information from user answers.

Original Task: {original_task}

Questions and Answers:
{qa_pairs}

Previous Analysis:
{previous_analysis}

Create an enhanced, comprehensive task description that:
1. Incorporates all the new information naturally
2. Maintains the original intent
3. Provides clear structure and organization
4. Includes all relevant details from the Q&A

Provide the restructured task in JSON format:
{{
    "restructured_task": "<comprehensive task description>",
    "key_additions": ["<list of key information added>"],
    "structure": {{
        "goal": "<primary objective>",
        "scope": "<what's included and excluded>",
        "requirements": ["<list of requirements>"],
        "constraints": ["<list of constraints>"],
        "success_criteria": ["<measurable outcomes>"],
        "target_audience": "<who this is for>",
        "dependencies": ["<external dependencies>"]
    }}
}}
"""

        self.prompt_polishing_template = """
Convert the refined task into a polished prompt suitable for agent orchestration.

Refined Task:
{refined_task}

Task Structure:
{task_structure}

Create a clear, actionable prompt that:
1. Clearly states the objective
2. Provides necessary context
3. Specifies deliverables
4. Includes constraints and requirements
5. Defines success criteria
6. Is formatted for optimal agent understanding

Provide the polished prompt in JSON format:
{{
    "polished_prompt": "<complete polished prompt>",
    "executive_summary": "<brief summary>",
    "key_deliverables": ["<list of deliverables>"],
    "agent_instructions": {{
        "primary_focus": "<main focus area>",
        "considerations": ["<important considerations>"],
        "quality_standards": ["<expected standards>"]
    }}
}}
"""
    
    async def analyze_task(self, task: str, session_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Main entry point for AI-based task analysis"""
        try:
            self.logger.info(f"[AI_TASK_ANALYZER] Starting analysis for session {session_id}")
            
            # Initialize analysis state
            state = TaskAnalysisState.INITIAL_ANALYSIS
            iteration_count = 0
            current_task = task
            analysis_history = []
            qa_history = []
            
            while iteration_count < self.max_iterations:
                iteration_count += 1
                self.logger.info(f"[AI_TASK_ANALYZER] Iteration {iteration_count}, State: {state.value}")
                
                # Step 1: Analyze task completeness
                analysis_result = await self._analyze_task_completeness(
                    current_task, 
                    session_id,
                    context=context
                )
                analysis_history.append(analysis_result)
                
                completeness_score = analysis_result.get("completeness_score", 0)
                self.logger.info(f"[AI_TASK_ANALYZER] Completeness score: {completeness_score}/10")
                
                # Check if we've reached target completeness
                if completeness_score >= self.target_completeness_score:
                    self.logger.info(f"[AI_TASK_ANALYZER] Target completeness reached!")
                    state = TaskAnalysisState.FINALIZING
                    break
                
                # Step 2: Generate questions for missing information
                state = TaskAnalysisState.GENERATING_QUESTIONS
                questions = await self._generate_clarifying_questions(
                    current_task,
                    analysis_result,
                    session_id
                )
                
                # Step 3: Return questions for user to answer
                # In a real implementation, this would pause and wait for user responses
                # For now, we'll return the questions and expect answers in the next call
                if questions:
                    return {
                        "state": "awaiting_answers",
                        "iteration": iteration_count,
                        "completeness_score": completeness_score,
                        "analysis": analysis_result,
                        "questions": questions,
                        "session_id": session_id,
                        "requires_user_input": True
                    }
                
                # If no questions generated (shouldn't happen), break
                break
            
            # Finalize and create polished prompt
            state = TaskAnalysisState.FINALIZING
            polished_result = await self._create_polished_prompt(
                current_task,
                analysis_history[-1] if analysis_history else None,
                session_id
            )
            
            state = TaskAnalysisState.COMPLETE
            
            return {
                "state": "complete",
                "success": True,
                "final_completeness_score": completeness_score,
                "iterations_used": iteration_count,
                "polished_prompt": polished_result.get("polished_prompt"),
                "executive_summary": polished_result.get("executive_summary"),
                "deliverables": polished_result.get("key_deliverables"),
                "analysis_history": analysis_history,
                "session_id": session_id
            }
            
        except Exception as e:
            self.logger.error(f"[AI_TASK_ANALYZER] Error in task analysis: {e}")
            return {
                "state": "error",
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    async def continue_with_answers(self, session_data: Dict[str, Any], answers: Dict[str, str]) -> Dict[str, Any]:
        """Continue analysis after receiving user answers"""
        try:
            session_id = session_data.get("session_id")
            current_task = session_data.get("current_task", "")
            questions = session_data.get("questions", [])
            previous_analysis = session_data.get("analysis")
            iteration = session_data.get("iteration", 1)
            
            self.logger.info(f"[AI_TASK_ANALYZER] Continuing analysis with user answers for session {session_id}")
            
            # Create Q&A pairs
            qa_pairs = self._format_qa_pairs(questions, answers)
            
            # Step 4: Restructure task with new information
            state = TaskAnalysisState.RESTRUCTURING_TASK
            restructured_result = await self._restructure_task(
                current_task,
                qa_pairs,
                previous_analysis,
                session_id
            )
            
            # Update current task
            current_task = restructured_result.get("restructured_task", current_task)
            
            # Step 5: Re-analyze the restructured task
            state = TaskAnalysisState.RE_ANALYZING
            return await self.analyze_task(
                current_task,
                session_id,
                context={
                    "iteration": iteration + 1,
                    "previous_analysis": previous_analysis,
                    "qa_history": qa_pairs
                }
            )
            
        except Exception as e:
            self.logger.error(f"[AI_TASK_ANALYZER] Error continuing with answers: {e}")
            return {
                "state": "error",
                "success": False,
                "error": str(e),
                "session_id": session_data.get("session_id")
            }
    
    async def _analyze_task_completeness(self, task: str, session_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze task completeness using AI"""
        try:
            # Format the analysis prompt
            prompt = self.analysis_prompt_template.format(
                task=task,
                context=json.dumps(context) if context else "None"
            )
            
            # Call Groq model through AI service
            self.logger.info(f"[AI_TASK_ANALYZER] Calling Groq model for completeness analysis")
            try:
                response = await ai_service.generate_content(
                    prompt=prompt,
                    provider_name="groq",
                    model=self.groq_model
                )
            except Exception as api_error:
                self.logger.error(f"[AI_TASK_ANALYZER] Groq API error: {api_error}")
                # Try to extract more details about the error
                if hasattr(api_error, 'response'):
                    self.logger.error(f"[AI_TASK_ANALYZER] Response status: {getattr(api_error.response, 'status_code', 'N/A')}")
                    self.logger.error(f"[AI_TASK_ANALYZER] Response body: {getattr(api_error.response, 'text', 'N/A')}")
                raise
            
            # Parse JSON response with robust handling
            analysis = self._parse_json_response(response, "completeness analysis")
            if analysis:
                self.logger.info(f"[AI_TASK_ANALYZER] Analysis complete: {analysis.get('completeness_score')}/10")
                return analysis
            else:
                # Return a default analysis if parsing fails
                return self._get_default_analysis(task)
        except Exception as e:
            self.logger.error(f"[AI_TASK_ANALYZER] Error in completeness analysis: {e}")
            raise
    
    async def _generate_clarifying_questions(self, task: str, analysis: Dict[str, Any], session_id: str) -> List[Dict[str, Any]]:
        """Generate clarifying questions based on analysis"""
        try:
            # Extract missing information from analysis
            missing_info = self._extract_missing_information(analysis)
            
            # Format the question generation prompt
            prompt = self.question_generation_prompt_template.format(
                task=task,
                analysis=json.dumps(analysis.get("analysis", {}), indent=2),
                missing_info=json.dumps(missing_info, indent=2)
            )
            
            # Call Groq model
            self.logger.info(f"[AI_TASK_ANALYZER] Generating clarifying questions")
            response = await ai_service.generate_content(
                prompt=prompt,
                provider_name="groq",
                model=self.groq_model
            )
            
            # Parse and return questions with robust handling
            result = self._parse_json_response(response, "question generation")
            if result:
                questions = result.get("questions", [])
                # Only return the first question to implement one-at-a-time approach
                if questions:
                    self.logger.info(f"[AI_TASK_ANALYZER] Generated {len(questions)} questions, returning first one")
                    return [questions[0]]  # Return only the first question
                else:
                    return []
            else:
                # Return default questions if parsing fails
                default_questions = self._get_default_questions(analysis)
                # Return only the first default question
                return [default_questions[0]] if default_questions else []
                
        except Exception as e:
            self.logger.error(f"[AI_TASK_ANALYZER] Error generating questions: {e}")
            default_questions = self._get_default_questions(analysis)
            # Return only the first default question
            return [default_questions[0]] if default_questions else []
    
    async def _restructure_task(self, original_task: str, qa_pairs: List[Dict[str, str]], 
                               previous_analysis: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Restructure task with new information from Q&A"""
        try:
            # Format the restructuring prompt
            prompt = self.task_restructuring_prompt_template.format(
                original_task=original_task,
                qa_pairs=json.dumps(qa_pairs, indent=2),
                previous_analysis=json.dumps(previous_analysis, indent=2)
            )
            
            # Call Groq model
            self.logger.info(f"[AI_TASK_ANALYZER] Restructuring task with new information")
            response = await ai_service.generate_content(
                prompt=prompt,
                provider_name="groq",
                model=self.groq_model
            )
            
            # Parse and return restructured task with robust handling
            result = self._parse_json_response(response, "task restructuring")
            if result:
                self.logger.info(f"[AI_TASK_ANALYZER] Task restructured successfully")
                return result
            else:
                # Return original task if parsing fails
                return {
                    "restructured_task": original_task,
                    "key_additions": [],
                    "structure": {}
                }
            
        except Exception as e:
            self.logger.error(f"[AI_TASK_ANALYZER] Error restructuring task: {e}")
            # Return original task if restructuring fails
            return {
                "restructured_task": original_task,
                "key_additions": [],
                "structure": {}
            }
    
    async def _create_polished_prompt(self, refined_task: str, final_analysis: Dict[str, Any], 
                                    session_id: str) -> Dict[str, Any]:
        """Create polished prompt for agent orchestration"""
        try:
            # Extract task structure from analysis
            task_structure = self._extract_task_structure(final_analysis)
            
            # Format the polishing prompt
            prompt = self.prompt_polishing_template.format(
                refined_task=refined_task,
                task_structure=json.dumps(task_structure, indent=2)
            )
            
            # Call Groq model
            self.logger.info(f"[AI_TASK_ANALYZER] Creating polished prompt")
            response = await ai_service.generate_content(
                prompt=prompt,
                provider_name="groq",
                model=self.groq_model
            )
            
            # Parse and return polished prompt with robust handling
            result = self._parse_json_response(response, "prompt polishing")
            if result:
                self.logger.info(f"[AI_TASK_ANALYZER] Polished prompt created")
                return result
            else:
                # Return a basic polished version if parsing fails
                return {
                    "polished_prompt": refined_task,
                    "executive_summary": "Task ready for execution",
                    "key_deliverables": ["Complete the specified task"],
                    "agent_instructions": {
                        "primary_focus": "Execute task as specified",
                        "considerations": [],
                        "quality_standards": ["High quality output"]
                    }
                }
            
        except Exception as e:
            self.logger.error(f"[AI_TASK_ANALYZER] Error creating polished prompt: {e}")
            # Return a basic polished version
            return {
                "polished_prompt": refined_task,
                "executive_summary": "Task ready for execution",
                "key_deliverables": ["Complete the specified task"],
                "agent_instructions": {
                    "primary_focus": "Execute task as specified",
                    "considerations": [],
                    "quality_standards": ["High quality output"]
                }
            }
    
    def _extract_missing_information(self, analysis: Dict[str, Any]) -> List[str]:
        """Extract key missing information from analysis"""
        missing_info = []
        
        # Get from overall assessment
        missing_info.extend(analysis.get("key_missing_information", []))
        
        # Extract from individual criteria
        criteria_analysis = analysis.get("analysis", {})
        for criterion, details in criteria_analysis.items():
            if details.get("score", 10) < 7:  # Focus on low-scoring areas
                missing_elements = details.get("missing_elements", [])
                missing_info.extend(missing_elements)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_missing = []
        for item in missing_info:
            if item not in seen:
                seen.add(item)
                unique_missing.append(item)
        
        return unique_missing[:10]  # Limit to top 10 items
    
    def _format_qa_pairs(self, questions: List[Dict[str, Any]], answers: Dict[str, str]) -> List[Dict[str, str]]:
        """Format questions and answers into pairs"""
        qa_pairs = []
        
        for question in questions:
            q_id = question.get("id")
            if q_id in answers:
                qa_pairs.append({
                    "question": question.get("question"),
                    "answer": answers[q_id],
                    "category": question.get("category"),
                    "purpose": question.get("purpose")
                })
        
        return qa_pairs
    
    def _extract_task_structure(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured information from analysis"""
        # This would extract and organize information from the analysis
        # For now, return a basic structure
        return {
            "completeness_score": analysis.get("completeness_score", 0),
            "strengths": self._identify_strengths(analysis),
            "gaps": self._identify_gaps(analysis),
            "recommendations": self._generate_recommendations(analysis)
        }
    
    def _identify_strengths(self, analysis: Dict[str, Any]) -> List[str]:
        """Identify strong areas from analysis"""
        strengths = []
        criteria_analysis = analysis.get("analysis", {})
        
        for criterion, details in criteria_analysis.items():
            if details.get("score", 0) >= 8:
                strengths.append(f"Strong {criterion}: {details.get('assessment', '')}")
        
        return strengths
    
    def _identify_gaps(self, analysis: Dict[str, Any]) -> List[str]:
        """Identify gaps from analysis"""
        gaps = []
        criteria_analysis = analysis.get("analysis", {})
        
        for criterion, details in criteria_analysis.items():
            if details.get("score", 10) < 7:
                gaps.append(f"{criterion.title()} needs improvement: {details.get('assessment', '')}")
        
        return gaps
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        overall_score = analysis.get("completeness_score", 0)
        
        if overall_score < 5:
            recommendations.append("Significant clarification needed across multiple areas")
        elif overall_score < 7:
            recommendations.append("Moderate clarification needed in key areas")
        else:
            recommendations.append("Minor refinements would enhance task clarity")
        
        return recommendations
    
    def _get_default_analysis(self, task: str) -> Dict[str, Any]:
        """Return default analysis structure when AI fails"""
        return {
            "completeness_score": 5,
            "analysis": {
                criterion: {
                    "score": 5,
                    "assessment": "Unable to analyze - using default",
                    "missing_elements": []
                }
                for criterion in ["clarity", "scope", "context", "requirements", 
                                "constraints", "success_criteria", "target_audience", "dependencies"]
            },
            "overall_assessment": "Task requires further analysis",
            "key_missing_information": ["Unable to determine - manual review needed"]
        }
    
    def _get_default_questions(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return intelligent default questions based on analysis when generation fails"""
        # Extract the lowest scoring areas from analysis
        low_score_areas = []
        if analysis and "analysis" in analysis:
            criteria_analysis = analysis.get("analysis", {})
            for criterion, details in criteria_analysis.items():
                score = details.get("score", 10)
                if score < 6:
                    low_score_areas.append((criterion, score, details.get("missing_elements", [])))
        
        # Sort by score (lowest first)
        low_score_areas.sort(key=lambda x: x[1])
        
        # Generate questions based on low-scoring areas
        questions = []
        question_id = 1
        
        # Map criteria to intelligent questions
        criteria_questions = {
            "clarity": [
                "What specific outcome or deliverable are you expecting from this task?",
                "Can you describe the main problem this task should solve?",
                "What does success look like for this task?"
            ],
            "scope": [
                "What should be included in this task, and what should be excluded?",
                "Are there any specific boundaries or limitations I should be aware of?",
                "How extensive should the solution be?"
            ],
            "context": [
                "What's the background or current situation that led to this task?",
                "Are there any existing systems or processes this needs to work with?",
                "What previous attempts have been made to address this?"
            ],
            "requirements": [
                "What are the must-have features or capabilities?",
                "Are there any technical specifications or standards to follow?",
                "What are the functional and non-functional requirements?"
            ],
            "constraints": [
                "What's the timeline or deadline for this task?",
                "Are there any budget or resource constraints?",
                "What technical or business limitations should I consider?"
            ],
            "success_criteria": [
                "How will we measure if this task is successful?",
                "What are the key performance indicators or metrics?",
                "What quality standards need to be met?"
            ],
            "target_audience": [
                "Who will be using or benefiting from this solution?",
                "What are their technical skill levels and expectations?",
                "Are there different user groups with different needs?"
            ],
            "dependencies": [
                "What external systems or services does this need to integrate with?",
                "Are there any prerequisite tasks or approvals needed?",
                "What other teams or stakeholders need to be involved?"
            ]
        }
        
        # Generate questions for low-scoring areas
        for criterion, score, missing_elements in low_score_areas[:3]:  # Top 3 problematic areas
            if criterion in criteria_questions:
                # Select the most relevant question based on missing elements
                question_text = criteria_questions[criterion][0]
                if missing_elements:
                    # Try to make the question more specific based on what's missing
                    for q in criteria_questions[criterion]:
                        if any(element.lower() in q.lower() for element in missing_elements):
                            question_text = q
                            break
                
                questions.append({
                    "id": f"q{question_id}",
                    "question": question_text,
                    "purpose": f"Address {criterion} issues (score: {score}/10)",
                    "category": criterion,
                    "priority": "high" if score < 4 else "medium"
                })
                question_id += 1
        
        # If no specific low-scoring areas or analysis failed, return general questions
        if not questions:
            questions = [
                {
                    "id": "q1",
                    "question": "What is the primary goal or outcome you want to achieve with this task?",
                    "purpose": "Clarify the main objective and expected results",
                    "category": "clarity",
                    "priority": "high"
                },
                {
                    "id": "q2",
                    "question": "Can you provide more context about why this task is needed and who will benefit from it?",
                    "purpose": "Understand background and stakeholders",
                    "category": "context",
                    "priority": "high"
                },
                {
                    "id": "q3",
                    "question": "What are the key requirements, constraints, and success criteria for this task?",
                    "purpose": "Define scope, limitations, and quality standards",
                    "category": "requirements",
                    "priority": "high"
                }
            ]
        
        self.logger.info(f"[AI_TASK_ANALYZER] Generated {len(questions)} intelligent fallback questions")
        return questions


    def _parse_json_response(self, response: str, context: str = "response") -> Optional[Dict[str, Any]]:
        """Parse JSON response with robust error handling
        
        Args:
            response: The raw response string from the AI model
            context: Context for logging (e.g., "completeness analysis")
            
        Returns:
            Parsed JSON dict or None if parsing fails
        """
        if not response:
            self.logger.error(f"[AI_TASK_ANALYZER] Empty response for {context}")
            return None
            
        # Clean the response
        cleaned_response = response.strip()
        
        # Handle markdown code blocks
        if cleaned_response.startswith('```'):
            self.logger.info(f"[AI_TASK_ANALYZER] Detected markdown code block in {context}")
            lines = cleaned_response.split('\n')
            json_lines = []
            in_json = False
            
            for line in lines:
                if line.strip().startswith('```json') or line.strip() == '```':
                    if line.strip().startswith('```json'):
                        in_json = True
                    else:
                        in_json = False
                    continue
                elif in_json:
                    json_lines.append(line)
            
            cleaned_response = '\n'.join(json_lines).strip()
            
        # Remove potential BOM or other invisible characters
        if cleaned_response.startswith('\ufeff'):
            cleaned_response = cleaned_response.lstrip('\ufeff')
            
        # Try to extract JSON if response contains extra text
        if cleaned_response and not cleaned_response.startswith('{') and not cleaned_response.startswith('['):
            # Try to find JSON in the response
            json_start = cleaned_response.find('{')
            json_array_start = cleaned_response.find('[')
            
            if json_start != -1 and (json_array_start == -1 or json_start < json_array_start):
                # Find matching closing brace
                brace_count = 0
                json_end = json_start
                for i in range(json_start, len(cleaned_response)):
                    if cleaned_response[i] == '{':
                        brace_count += 1
                    elif cleaned_response[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
                cleaned_response = cleaned_response[json_start:json_end]
            elif json_array_start != -1:
                # Find matching closing bracket
                bracket_count = 0
                json_end = json_array_start
                for i in range(json_array_start, len(cleaned_response)):
                    if cleaned_response[i] == '[':
                        bracket_count += 1
                    elif cleaned_response[i] == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            json_end = i + 1
                            break
                cleaned_response = cleaned_response[json_array_start:json_end]
        
        # Attempt to parse JSON
        try:
            result = json.loads(cleaned_response)
            self.logger.info(f"[AI_TASK_ANALYZER] Successfully parsed JSON for {context}")
            return result
        except json.JSONDecodeError as e:
            self.logger.error(f"[AI_TASK_ANALYZER] Failed to parse JSON for {context}: {e}")
            self.logger.error(f"[AI_TASK_ANALYZER] Response preview: {cleaned_response[:200]}...")
            self.logger.error(f"[AI_TASK_ANALYZER] JSON error position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
            
            # Log the actual character at error position for debugging
            if hasattr(e, 'pos') and e.pos < len(cleaned_response):
                error_context = cleaned_response[max(0, e.pos-20):e.pos+20]
                self.logger.error(f"[AI_TASK_ANALYZER] Error context: ...{repr(error_context)}...")
            
            return None


# Create global instance
ceo_ai_task_analyzer = CEOAITaskAnalyzer()