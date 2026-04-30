# Frontend State Management Architecture for Agent Outputs

## Current State Analysis

After analyzing the existing frontend codebase:

### Current Architecture:
- **React-based frontend** with functional components
- **No existing state management library** (no Redux, Zustand, or Context API for agent data)
- **Local component state** used in Dashboard.jsx for agent outputs
- **Basic API client** in `/src/lib/api.js` without logging capabilities
- **Agent outputs stored temporarily** in component state (`agentResults` array)

### Key Issues Identified:
1. **No persistent state management** - Agent outputs are lost on component unmount
2. **No cross-agent data sharing** - Each agent execution is isolated
3. **No API request/response logging** - Makes debugging difficult
4. **Content Writer output not captured** - The `output` attribute is not extracted and saved
5. **No session management** - No way to track agent outputs across sessions

## Proposed State Management Architecture

### 1. Technology Stack
- **Zustand** - Lightweight state management library (simpler than Redux)
- **React Query** - For API state management and caching
- **Custom Logging Middleware** - For comprehensive API logging

### 2. State Structure

```javascript
// Agent State Store Structure
{
  // Session Management
  sessions: {
    current: 'session-uuid',
    history: ['session-1', 'session-2']
  },
  
  // Agent Outputs by Session
  agentOutputs: {
    'session-uuid': {
      'content_writer': {
        request_id: 'req-123',
        agent_id: 'content_writer',
        output: '🚀 Upskill with GenAI...', // The actual content
        timestamp: '2026-04-30T10:50:06.443Z',
        metadata: {},
        raw_response: {} // Full API response
      },
      'social_publisher': {
        request_id: 'req-456',
        agent_id: 'social_publisher',
        input_from: 'content_writer', // Track data source
        output: { post_id: 'ig_123', status: 'published' },
        timestamp: '2026-04-30T10:50:17.714Z'
      }
    }
  },
  
  // API Logs
  apiLogs: [
    {
      id: 'log-1',
      type: 'request',
      method: 'POST',
      url: '/api/agents/content_writer',
      payload: {},
      timestamp: '2026-04-30T10:50:03.506Z'
    },
    {
      id: 'log-2',
      type: 'response',
      status: 200,
      url: '/api/agents/content_writer',
      data: { output: '...' },
      timestamp: '2026-04-30T10:50:06.443Z'
    }
  ],
  
  // Orchestration State
  orchestration: {
    currentPlan: {},
    executionStatus: 'idle' | 'running' | 'completed',
    currentStep: 0,
    totalSteps: 0
  }
}
```

### 3. Key Components

#### A. State Store (`/src/store/agentStore.js`)
- Centralized Zustand store for all agent-related state
- Actions for saving/retrieving agent outputs
- Session management functions

#### B. API Logging Middleware (`/src/middleware/apiLogger.js`)
- Intercepts all API calls
- Logs requests and responses
- Extracts and saves agent outputs

#### C. Agent Output Manager (`/src/services/agentOutputManager.js`)
- Handles extraction of `output` attribute from responses
- Manages cross-agent data sharing
- Provides helper functions for accessing previous agent outputs

#### D. Flow Visibility Component (`/src/components/FlowVisibility.jsx`)
- Real-time display of API logs
- Visual representation of data flow
- Debug console for agent outputs

### 4. Data Flow

1. **CEO Agent** initiates orchestration
2. **API Logger** captures all requests/responses
3. **Content Writer** execution:
   - Response captured by logger
   - `output` attribute extracted and saved to store
   - Session-based storage for persistence
4. **Social Publisher** execution:
   - Retrieves Content Writer output from store
   - Uses content for Instagram caption
   - Execution logged and stored

### 5. Implementation Benefits

- **Complete visibility** into agent communication
- **Persistent storage** of agent outputs
- **Cross-agent data sharing** enabled
- **Comprehensive debugging** capabilities
- **Session-based tracking** for better user experience

## Next Steps

1. Install required dependencies (Zustand, React Query)
2. Implement the state store structure
3. Create API logging middleware
4. Build agent output management system
5. Develop flow visibility components
6. Integrate with existing Dashboard component
7. Add comprehensive testing