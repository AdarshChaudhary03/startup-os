# Frontend CEO Chat Integration Guide

## Overview

This guide explains the CEO agent chat functionality integration in the frontend application. The chat interface replaces the direct orchestrate endpoint call with an interactive conversation where the CEO agent asks 3-5 clarifying questions before creating a plan and delegating to other agents.

## Architecture Changes

### Previous Flow
1. User enters task in CommandBar
2. Frontend directly calls `orchestrate` endpoint
3. CEO agent processes and delegates immediately

### New Flow
1. User enters task in CommandBar
2. CEO Chat Interface opens
3. CEO agent asks clarifying questions
4. User provides answers
5. CEO finalizes requirements
6. Plan is created and agents are delegated

## Components

### 1. CEOChatInterface Component
**Location:** `/src/components/CEOChatInterface.jsx`

**Features:**
- Modal-based chat interface
- Real-time message display
- Loading states and animations
- Requirements summary display
- Auto-scroll to latest messages
- Error handling

**Props:**
- `onClose`: Function to close the chat interface
- `onRequirementsFinalized`: Callback when requirements are complete
- `initialMessage`: Optional initial message to start conversation

### 2. useCEOChat Hook
**Location:** `/src/hooks/useCEOChat.js`

**Features:**
- Manages conversation state
- Handles API calls
- Tracks messages and requirements
- Provides loading and error states

**Methods:**
- `startConversation(message)`: Start a new conversation
- `sendMessage(message)`: Send a message in active conversation
- `getState()`: Get current conversation state
- `finalizeRequirements()`: Finalize and get the plan
- `reset()`: Reset all state

## API Integration

### New API Functions
**Location:** `/src/lib/api.js`

```javascript
// Start a new CEO chat conversation
startCEOChat(task)

// Send a message in the conversation
sendCEOChatMessage(conversationId, message)

// Get current conversation state
getCEOChatState(conversationId)

// Finalize requirements and get plan
finalizeCEORequirements(conversationId)
```

## Dashboard Integration

### Modified Files
1. **Dashboard.jsx**
   - Added `showCEOChat` and `initialChatMessage` state
   - Modified `runTask` to open chat instead of direct orchestration
   - Added `handleChatRequirementsFinalized` to process finalized requirements
   - Integrated CEOChatInterface component

### Key Changes
```javascript
// Old approach
const plan = await getOrchestrationPlan({ task, agent_id });

// New approach
setShowCEOChat(true);
setInitialChatMessage(task);
// ... chat interaction ...
handleChatRequirementsFinalized({ requirements, plan, conversationId });
```

## Usage Example

1. User types: "Build a dashboard for our product"
2. CEO Chat opens with this message
3. CEO asks: "What is the primary purpose of this dashboard?"
4. User responds: "To track user analytics and engagement"
5. CEO asks: "Who is the target audience?"
6. User responds: "Product managers and executives"
7. CEO asks: "What are the key metrics you want to display?"
8. User responds: "User growth, retention, and feature adoption"
9. CEO finalizes requirements and creates plan
10. Dashboard executes the plan with delegated agents

## Testing

### Test Files
1. **CEOChatInterface.test.jsx** - Component tests
2. **useCEOChat.test.js** - Hook tests

### Running Tests
```bash
npm test
# or
npm run test:watch
```

## Backend Requirements

The frontend expects these endpoints to be available:
- `POST /api/ceo/chat/start`
- `POST /api/ceo/chat/message`
- `GET /api/ceo/chat/{conversationId}/state`
- `POST /api/ceo/chat/{conversationId}/finalize`

## Environment Variables

```env
REACT_APP_API_URL=http://localhost:8000
```

## Future Enhancements

1. **Conversation History**: Store and display previous conversations
2. **Templates**: Pre-defined requirement templates for common tasks
3. **Voice Integration**: Combine with voice mode for hands-free interaction
4. **Multi-language Support**: Support for conversations in different languages
5. **Rich Media**: Support for images, diagrams in chat
6. **Export**: Export requirements and plans as documents

## Troubleshooting

### Common Issues

1. **Chat not opening**: Check if `showCEOChat` state is properly set
2. **API errors**: Verify backend endpoints are running and accessible
3. **Message not sending**: Check conversation state and loading flags
4. **Requirements not finalizing**: Ensure conversation reaches 'requirements_complete' state

### Debug Mode

Add to localStorage for debug logs:
```javascript
localStorage.setItem('CEO_CHAT_DEBUG', 'true');
```