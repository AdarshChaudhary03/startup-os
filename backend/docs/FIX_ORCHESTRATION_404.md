# Fix for Orchestration 404 Error

## Issue Summary
The CEO agents (ceo_simplified_flow and ceo_conversation_flow) were encountering a 404 "Not Found" error when trying to access the `/api/orchestrate` endpoint.

## Error Details
```
2026-05-01 09:20:31,071 - src.agents.ceo.ceo_simplified_flow - ERROR - [CEO_SIMPLIFIED] Orchestration error: Orchestration failed with status 404: {"detail":"Not Found"}
2026-05-01 09:20:31,072 - src.agents.ceo.ceo_conversation_flow - ERROR - [CEO_CHAT_DEBUG] Failed to get orchestration plan: Orchestration failed with status 404: {"detail":"Not Found"}
```

## Root Cause
The orchestration routes were not being registered in the FastAPI application. The `orchestration_router` from `orchestration_routes.py` was not imported or included in the `server.py` file.

## Solution Applied

### 1. Added Import Statement
Added the missing import in `server.py`:
```python
from src.routes.orchestration_routes import orchestration_router
```

### 2. Registered Router
Added the orchestration router to the FastAPI app:
```python
app.include_router(orchestration_router)  # Add orchestration routes for /api/orchestrate endpoint
```

## Available Orchestration Endpoints
After the fix, the following endpoints are now available:
- `POST /api/orchestrate` - Main orchestration planning endpoint
- `POST /api/orchestrate/plan` - Alias for orchestration planning
- `POST /api/orchestrate/legacy` - Legacy endpoint for backward compatibility

## How CEO Agents Use Orchestration

### CEO Simplified Flow
1. Formats requirements into a polished prompt
2. Calls `/api/orchestrate` to get an execution plan
3. Receives a plan with steps containing:
   - Agent IDs and names
   - Instructions for each agent
   - Endpoints to call for each agent
4. Executes agents sequentially based on the plan

### CEO Conversation Flow
1. Gathers requirements through conversation
2. Finalizes requirements and creates polished prompt
3. Uses simplified_ceo_agent to call `/api/orchestrate`
4. Returns the orchestration plan for execution

## Verification
After applying this fix:
1. The `/api/orchestrate` endpoint should return 200 OK instead of 404
2. CEO agents should successfully receive orchestration plans
3. The orchestration flow should proceed to agent execution

## Additional Notes
- The orchestration router uses the prefix `/api` which is why the full path is `/api/orchestrate`
- The endpoint returns an `OrchestrationPlanResponse` with execution steps
- Each step includes the agent endpoint to call for real-time progress tracking
