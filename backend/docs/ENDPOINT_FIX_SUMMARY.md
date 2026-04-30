# Social Media Publisher Endpoint Fix Summary

## Problem
The CEO agent was getting a 404 error when trying to call `/api/agents/social_publisher` endpoint because:
1. The orchestration service was returning `social_publisher` as the agent ID
2. The agent routes had multiple endpoint formats (hyphenated and underscore)
3. There was no `/api/agents/social_publisher` endpoint defined

## Solution Implemented

### 1. Standardized Agent Endpoints (agent_routes.py)
- Changed all agent endpoints to use underscore format consistently
- Removed duplicate endpoints with different formats
- Added `/api/agents/social_publisher` endpoint that was missing
- Each agent now has exactly one endpoint: `/api/agents/{agent_id}`

### 2. Fixed Orchestration Response (orchestration_routes.py)
- Updated orchestration to return endpoints in underscore format
- Changed from: `endpoint_path = f"/api/agents/{agent_obj['id'].replace('_', '-')}"`
- Changed to: `endpoint_path = f"/api/agents/{agent_obj['id']}"`

### 3. Updated CEO Simplified Flow (ceo_simplified_flow.py)
- Updated agent endpoint mappings to use underscore format
- Changed `social_publisher` endpoint from `/api/agents/social-media-publisher` to `/api/agents/social_publisher`
- Changed `content_writer` endpoint from `/api/agents/content-writer` to `/api/agents/content_writer`

## Key Changes

### Before:
```python
# Multiple endpoint formats
@agent_router.post("/social-media-publisher", ...)
@agent_router.post("/social-publisher", ...)
@agent_router.post("/social_media_publisher", ...)
# Missing: /social_publisher
```

### After:
```python
# Single standardized endpoint
@agent_router.post("/social_publisher", ...)
```

## Testing

To verify the fix:

1. Start the backend server:
   ```bash
   cd /startup-os/backend
   python server.py
   ```

2. Test the social publisher endpoint:
   ```bash
   curl -X POST http://localhost:8000/api/agents/social_publisher \
     -H "Content-Type: application/json" \
     -d '{"task": "Test social media publishing"}'
   ```

3. Test orchestration returns correct endpoints:
   ```bash
   curl -X POST http://localhost:8000/api/orchestrate \
     -H "Content-Type: application/json" \
     -d '{"task": "Create and publish a social media post"}'
   ```

4. Verify all agents have single endpoints:
   ```bash
   curl http://localhost:8000/api/agents/list
   ```

## Expected Results

1. The `/api/agents/social_publisher` endpoint should return 200 OK (not 404)
2. Orchestration should return steps with endpoints like `/api/agents/social_publisher`
3. CEO agent should successfully delegate tasks to social media publisher
4. Content from content writer should be passed to social media publisher

## Files Modified

1. **agent_routes.py**: Standardized all endpoints to underscore format
2. **orchestration_routes.py**: Fixed endpoint generation to match agent routes
3. **ceo_simplified_flow.py**: Updated endpoint mappings
4. **test_agent_endpoints.py**: Created comprehensive test suite

## Next Steps

1. Restart the backend server to apply changes
2. Test the CEO agent flow with social media publishing task
3. Verify no more 404 errors occur
4. Ensure content is properly passed between agents