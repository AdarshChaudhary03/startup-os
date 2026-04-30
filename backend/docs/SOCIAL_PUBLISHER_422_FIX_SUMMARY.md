# Social Media Publisher 422 Error Fix Summary

## Issue Analysis

The 422 Unprocessable Content error occurs when the backend validation fails for the social media publisher request. After analyzing the code:

### Frontend Payload Structure
The frontend sends:
```javascript
{
  task: "Schedule and publish the caption on Instagram.",
  context: {
    content_writer_output: "🤖 Discover the power of AI with GenAI...",
    caption: "🤖 Discover the power of AI with GenAI...",
    metadata: {...}
  },
  metadata: {
    step_number: 2,
    total_steps: 2,
    session_id: 'session-1777533420715-ygafy0x8i'
  },
  caption: "🤖 Discover the power of AI with GenAI...",
  content: "🤖 Discover the power of AI with GenAI..."
}
```

### Backend Expectations
The backend `AgentExecutionRequest` model expects:
```python
class AgentExecutionRequest(BaseModel):
    task: str
    context: Optional[Any] = None  # Can be string or dict
    metadata: Optional[dict] = None
    caption: Optional[str] = None
    content: Optional[str] = None
```

### The Problem
The 422 error is likely caused by:
1. The backend FastAPI validation is failing on the request body
2. The social media publisher main agent is receiving the task instruction ("Schedule and publish...") instead of the actual content
3. The content extraction logic in the backend is not properly handling the nested context structure

### Root Cause
In `utils.py`, the `execute_agent_real` function for social_publisher is extracting content from the wrong fields. It's using the task field which contains the instruction, not the actual generated content.

## Solution

The fix needs to be applied in the backend to properly extract the caption/content from the request payload.