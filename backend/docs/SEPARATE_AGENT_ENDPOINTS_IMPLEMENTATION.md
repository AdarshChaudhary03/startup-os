# Separate Agent Endpoints Implementation Plan

## Current Issue
Currently all agents are processing under the `/orchestrate` endpoint. We need to create separate endpoints for all agents to enable real-time progress tracking and better frontend integration.

## Implementation Plan

### 1. Current Architecture
- Single `/orchestrate` endpoint handles all agent execution
- CEO agent plans and executes all agents sequentially
- Frontend receives final result only
- No real-time progress visibility

### 2. New Architecture
- Separate endpoint for each agent type
- CEO agent calls `/orchestrate` to get orchestration plan
- For each step in the plan, frontend calls specific agent endpoint
- Real-time progress updates for each agent execution
- CEO agent receives responses and coordinates next steps

### 3. Endpoint Structure
```
/api/orchestrate          - Returns orchestration plan only
/api/agents/content-writer - Content Writer Agent endpoint
/api/agents/social-publisher - Social Media Publisher Agent endpoint
/api/agents/seo-specialist - SEO Specialist Agent endpoint
/api/agents/ad-copywriter - Ad Copywriter Agent endpoint
... (one for each agent)
```

### 4. Workflow
1. Frontend calls `/api/orchestrate` with task
2. CEO agent returns orchestration plan with steps
3. For each step in plan:
   - Frontend calls specific agent endpoint
   - Agent processes and returns result
   - Frontend shows real-time progress
   - Result passed to next agent if sequential
4. Final aggregated result displayed

### 5. Benefits
- Real-time progress tracking
- Better error handling per agent
- Scalable architecture
- Independent agent testing
- Better frontend UX

## Implementation Steps
1. Create agent routes module
2. Implement individual agent endpoints
3. Modify orchestrate endpoint to return plan only
4. Update frontend to handle multi-step execution
5. Add progress tracking and error handling
