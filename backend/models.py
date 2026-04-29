from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class OrchestrateRequest(BaseModel):
    task: str
    agent_id: Optional[str] = None  # if user picked specific agent via template


class StepLog(BaseModel):
    actor: str
    message: str
    status: str  # info | thinking | working | success
    timestamp: str


class AgentRun(BaseModel):
    agent_id: str
    agent_name: str
    team_id: str
    team_name: str
    instruction: str
    output: str


class AgentExecutionRequest(BaseModel):
    task: str
    context: Optional[str] = None  # Optional context from previous agents
    metadata: Optional[dict] = None  # Optional metadata for agent execution


class AgentExecutionResponse(BaseModel):
    request_id: str
    agent_id: str
    agent_name: str
    team_id: str
    team_name: str
    task: str
    output: str
    success: bool
    duration_ms: int
    timestamp: str
    error: Optional[str] = None
    metadata: Optional[dict] = None


class OrchestrationPlanStep(BaseModel):
    agent_id: str
    agent_name: str
    team_id: str
    team_name: str
    instruction: str
    endpoint: str  # The endpoint to call for this agent


class OrchestrationPlanResponse(BaseModel):
    request_id: str
    task: str
    mode: str  # "single" | "sequential" | "parallel"
    rationale: str
    steps: List[OrchestrationPlanStep]
    total_steps: int
    used_llm: bool


class OrchestrationStatusResponse(BaseModel):
    request_id: str
    task: str
    mode: str
    total_steps: int
    completed_steps: int
    current_step: Optional[int] = None
    current_agent: Optional[str] = None
    status: str  # "planning" | "executing" | "completed" | "failed"
    agent_results: List[AgentExecutionResponse] = []
    created_at: str
    updated_at: str


class OrchestrateResponse(BaseModel):
    request_id: str
    task: str
    mode: str  # "single" | "sequential" | "parallel"
    rationale: str
    chosen_agent_id: str           # primary agent (first in plan) — kept for backwards compat
    chosen_agent_name: str
    team_id: str
    team_name: str
    agent_runs: List[AgentRun]      # all agents involved (1 to N)
    steps: List[StepLog]
    output: str                     # primary output (first agent_run) — kept for backwards compat
    duration_ms: int
    used_llm: bool                  # True if Claude planned the route, False if fallback


class CEOOrchestrationRequest(BaseModel):
    task: str
    priority: Optional[str] = "normal"  # "low" | "normal" | "high" | "urgent"
    context: Optional[str] = None  # Additional context for CEO analysis
    metadata: Optional[dict] = None  # Optional metadata for orchestration


class CEOOrchestrationResponse(BaseModel):
    request_id: str
    task: str
    mode: str
    rationale: str
    agent_results: List[AgentExecutionResponse]
    final_output: str
    total_duration_ms: int
    timestamp: str
    success: bool
    learning_applied: Optional[Dict[str, Any]] = None
    metadata: Optional[dict] = None


class CEOAnalysisResponse(BaseModel):
    request_id: str
    agent_name: str
    analysis: str  # CEO's analysis of the agent output
    recommendations: Optional[str] = None  # CEO's recommendations
    next_agent_context: Optional[str] = None  # Context prepared for next agent
    timestamp: str


# CEO Requirements Gathering Models
class CEORequirementsRequest(BaseModel):
    task: str
    user_context: Optional[Dict[str, Any]] = None  # Additional user context
    priority: Optional[str] = "normal"  # "low" | "normal" | "high" | "urgent"


class CEOClarificationRequest(BaseModel):
    session_id: str
    clarifications: Dict[str, str]  # Question -> Answer mapping


class CEORequirementAnalysis(BaseModel):
    completeness_score: int  # 1-10 rating
    missing_categories: List[Dict[str, Any]]
    clarity_issues: List[str]
    ready_to_proceed: bool
    next_action: str


class CEOPolishedRequirement(BaseModel):
    polished_task: str
    objective: str
    target_audience: str
    deliverables: List[str]
    success_criteria: List[str]
    constraints: List[str]
    timeline: str
    additional_context: str
    agent_plan_suggestion: str


class CEORequirementsResponse(BaseModel):
    session_id: str
    request_id: str
    status: str  # "awaiting_clarification" | "requirements_complete" | "orchestration_complete"
    message: str
    analysis: Optional[CEORequirementAnalysis] = None
    clarification_questions: List[str] = []
    polished_requirement: Optional[CEOPolishedRequirement] = None
    similar_requirements: List[Dict[str, Any]] = []
    next_action: str  # "provide_clarifications" | "proceed_to_orchestration"
    timestamp: str


class CEOClarificationResponse(BaseModel):
    session_id: str
    request_id: str
    status: str
    message: str
    additional_questions: List[str] = []
    ready_to_proceed: bool
    timestamp: str


class CEORequirementLearning(BaseModel):
    original_task: str
    clarifications: Dict[str, str]
    polished_requirement: Dict[str, Any]
    timestamp: str
    request_id: str
    similarity_score: Optional[float] = None