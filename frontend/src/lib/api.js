// API client for the AI Startup OS backend

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// Helper function for API calls
async function apiCall(endpoint, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    let errorMessage;
    try {
      const errorData = await response.json();
      errorMessage =
        errorData.detail ||
        errorData.message ||
        `API call failed: ${response.statusText}`;
    } catch (e) {
      errorMessage = `API call failed: ${response.statusText}`;
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

// Fetch teams and agents
export async function fetchTeams() {
  return apiCall("/api/teams");
}

// Get orchestration plan from CEO
export async function getOrchestrationPlan({ task, agent_id = null }) {
  return apiCall("/api/ceo/plan", {
    method: "POST",
    body: JSON.stringify({ task, agent_id }),
  });
}

// Execute a specific agent with state management integration
export async function executeAgent(agentId, payload, sessionId = null) {
  // Import agent output manager dynamically to avoid circular dependencies
  const { default: agentOutputManager } =
    await import("../services/agentOutputManager");
  const { useAgentStore } = await import("../store/agentStore");

  // Get or create session
  const store = useAgentStore.getState();
  const agentActions = store.actions;
  let currentSession = sessionId || store.sessions.current;

  if (!currentSession) {
    // Create new session if none exists
    const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    agentActions.createSession(newSessionId);
    // Update currentSession to use the newly created session
    const updatedStore = useAgentStore.getState();
    currentSession = newSessionId;
  }

  // Build context with previous agent outputs
  const context = agentOutputManager.buildAgentContext(agentId, currentSession);

  // Enhanced payload with context and session info
  // CRITICAL FIX: Don't stringify context for social_publisher - pass it as an object
  const enhancedPayload = {
    ...payload,
    // For social_publisher, pass context directly to preserve structure
    context:
      (agentId === "social_publisher" ||
        agentId === "social-media-publisher") &&
      context
        ? context
        : context
          ? JSON.stringify(context)
          : payload.context,
    metadata: {
      ...payload.metadata,
      session_id: currentSession,
    },
  };

  // For social_publisher, also add caption directly to payload
  if (
    (agentId === "social_publisher" || agentId === "social-media-publisher") &&
    context
  ) {
    if (context.caption) {
      enhancedPayload.caption = context.caption;
    }
    if (context.content_writer_output) {
      enhancedPayload.content = context.content_writer_output;
    }
  }

  console.log(`[API] Executing agent ${agentId} with enhanced context:`, {
    hasContentWriterOutput: !!context?.content_writer_output,
    sessionId: currentSession,
  });

  // Execute with monitoring
  const executionPromise = apiCall(`/api/agents/${agentId}`, {
    method: "POST",
    body: JSON.stringify(enhancedPayload),
  });

  return agentOutputManager.monitorAgentExecution(
    agentId,
    enhancedPayload,
    executionPromise,
  );
}

// Legacy orchestrate function (to be replaced with CEO chat)
export async function orchestrate({ task, agent_id = null }) {
  return apiCall("/api/orchestrate", {
    method: "POST",
    body: JSON.stringify({ task, agent_id }),
  });
}

// NEW: CEO Chat API functions
export async function startCEOChat(task) {
  return apiCall("/api/ceo/chat/start", {
    method: "POST",
    body: JSON.stringify({ initial_message: task }),
  });
}

export async function sendCEOChatMessage(conversationId, message) {
  return apiCall("/api/ceo/chat/message", {
    method: "POST",
    body: JSON.stringify({
      conversation_id: conversationId,
      message: message,
    }),
  });
}

export async function getCEOChatState(conversationId) {
  return apiCall(`/api/ceo/chat/${conversationId}/state`);
}

export async function finalizeCEORequirements(conversationId) {
  return apiCall(`/api/ceo/chat/${conversationId}/finalize`, {
    method: "POST",
  });
}

// NEW: Orchestrate with polished prompt
export async function orchestrateWithPrompt(polishedPrompt) {
  return apiCall("/api/orchestrate", {
    method: "POST",
    body: JSON.stringify({ task: polishedPrompt }),
  });
}
