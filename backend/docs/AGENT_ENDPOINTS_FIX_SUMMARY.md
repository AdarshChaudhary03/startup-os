# Agent Endpoints Fix Summary

## Issue
CEO agent was getting 404 error when trying to delegate tasks to agents:
- Error: `POST /api/agents/content_writer` returning 404
- The CEO agent was trying to call endpoints with underscore format but only hyphen format was available

## Root Cause
The agent endpoints were only configured with hyphen format (e.g., `/api/agents/content-writer`) but the CEO agent was trying to call them with underscore format (e.g., `/api/agents/content_writer`).

## Solution Implemented

### 1. Added Underscore Format Endpoints
Updated `agent_routes.py` to support both URL formats:
- Original: `/api/agents/content-writer` 
- Added: `/api/agents/content_writer`

### 2. Specific Changes Made

#### For content_writer agent:
```python
# Added underscore format endpoint
@agent_router.post("/content_writer", response_model=AgentExecutionResponse)
async def execute_content_writer_underscore(req: AgentExecutionRequest, request: Request):
    """Execute Content Writer Agent with real LLM integration (underscore format)."""
    return await execute_agent("content_writer", req, request)
```

#### For all other agents:
Added underscore format endpoints for all 19 agents:
- social_media_publisher
- seo_specialist
- ad_copywriter
- analytics_agent
- frontend_engineer
- backend_engineer
- devops_agent
- qa_agent
- architect_agent
- lead_researcher
- outreach_agent
- demo_agent
- negotiator_agent
- crm_agent
- user_researcher
- pm_agent
- designer_agent
- roadmap_agent
- feedback_agent

### 3. Updated Agent List Endpoint
Modified the `/api/agents/list` endpoint to return both endpoint formats:
```python
"endpoint": endpoint_path,  # Hyphen format
"endpoint_underscore": endpoint_path_underscore  # Underscore format
```

### 4. Test Suite Created
Created comprehensive test suite in `tests/test_agent_endpoints_delegation.py` to verify:
- Both underscore and hyphen endpoints work
- CEO delegation to agents works correctly
- Error handling is proper
- All agent endpoints are accessible

## How CEO Agent Should Call Endpoints

The CEO agent can now successfully delegate tasks using either format:

### Example 1: Using underscore format (recommended for consistency)
```python
endpoint = "/api/agents/content_writer"
payload = {
    "task": "Write a blog post about AI"
}
```

### Example 2: Using hyphen format (also supported)
```python
endpoint = "/api/agents/content-writer"
payload = {
    "task": "Write a blog post about AI"
}
```

## Testing Instructions

1. Start the backend server:
   ```bash
   cd startup-os/backend
   python server.py
   ```

2. Test the endpoints:
   ```bash
   # Test content_writer endpoint with underscore
   curl -X POST http://localhost:8000/api/agents/content_writer \
     -H "Content-Type: application/json" \
     -d '{"task": "Write a test message"}'
   
   # Test list of all agents
   curl http://localhost:8000/api/agents/list
   ```

3. Run the test suite:
   ```bash
   python -m pytest tests/test_agent_endpoints_delegation.py -v
   ```

## Result
The 404 error is now fixed. CEO agent can successfully delegate tasks to all agents using either underscore or hyphen format endpoints.