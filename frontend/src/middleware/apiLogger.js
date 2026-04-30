// API Logging Middleware for comprehensive request/response tracking
import { useAgentStore } from "../store/agentStore";

// Create a wrapper around fetch to log all API calls
const originalFetch = window.fetch;

// Enhanced fetch with logging
window.fetch = async function (...args) {
  const [resource, config] = args;
  const startTime = Date.now();

  // Get agent actions for logging
  const agentActions = useAgentStore.getState().actions;

  // Parse URL and request details
  const url = typeof resource === "string" ? resource : resource.url;
  const method = config?.method || "GET";
  const payload = config?.body ? JSON.parse(config.body) : null;
  const headers = config?.headers || {};

  // Log the request
  const requestId = agentActions.logApiRequest({
    url,
    method,
    payload,
    headers,
  });

  // Special logging for agent endpoints
  if (url.includes("/api/agents/")) {
    const agentId = url.split("/").pop();
    console.log(`[API Logger] Agent request to ${agentId}:`, {
      task: payload?.task,
      context: payload?.context,
      metadata: payload?.metadata,
    });
  }

  try {
    // Make the actual request
    const response = await originalFetch(...args);
    const duration = Date.now() - startTime;

    // Clone response BEFORE any other operations to avoid body stream issues
    let responseClone;
    let responseData = null;

    // Only clone if response is ok and has a body
    if (response.ok && response.body && !response.bodyUsed) {
      try {
        responseClone = response.clone();
      } catch (cloneError) {
        console.warn("[API Logger] Failed to clone response:", cloneError);
      }
    }

    // Try to read response data if we have a clone
    if (responseClone) {
      try {
        responseData = await responseClone.json();
      } catch (e) {
        // Response might not be JSON
        responseData = await responseClone.text();
      }
    }

    // Log the response
    agentActions.logApiResponse(requestId, {
      status: response.status,
      url,
      data: responseData,
      duration,
      error: !response.ok ? response.statusText : null,
    });

    // Special handling for Content Writer responses
    if (url.includes("/api/agents/content_writer") && responseData?.output) {
      console.log("[API Logger] Content Writer output detected:");
      console.log("- Output length:", responseData.output.length);
      console.log(
        "- Output preview:",
        responseData.output.substring(0, 200) + "...",
      );
      console.log("- Full response:", responseData);
    }

    // Special handling for Social Media Publisher
    if (url.includes("/api/agents/social_publisher")) {
      console.log("[API Logger] Social Media Publisher request:");
      console.log("- Task:", payload?.task);
      console.log("- Context:", payload?.context);
      console.log("- Should contain Content Writer output in context");
    }

    return response;
  } catch (error) {
    const duration = Date.now() - startTime;

    // Log the error
    agentActions.logApiResponse(requestId, {
      status: 0,
      url,
      error: error.message,
      duration,
    });

    throw error;
  }
};

// API Logger utility class
class APILogger {
  static logAgentInteraction(fromAgent, toAgent, data) {
    console.log(`[Agent Interaction] ${fromAgent} → ${toAgent}:`, {
      timestamp: new Date().toISOString(),
      data: typeof data === "string" ? data.substring(0, 100) + "..." : data,
    });
  }

  static logOrchestrationStep(step, totalSteps, agent, instruction) {
    console.log(`[Orchestration] Step ${step}/${totalSteps}:`, {
      agent,
      instruction,
      timestamp: new Date().toISOString(),
    });
  }

  static logStateUpdate(type, data) {
    console.log(`[State Update] ${type}:`, {
      timestamp: new Date().toISOString(),
      data,
    });
  }

  static createRequestLogger(component) {
    return {
      logRequest: (endpoint, payload) => {
        console.log(`[${component}] API Request:`, {
          endpoint,
          payload,
          timestamp: new Date().toISOString(),
        });
      },

      logResponse: (endpoint, response, duration) => {
        console.log(`[${component}] API Response:`, {
          endpoint,
          status: response.status || "success",
          duration: `${duration}ms`,
          data: response.data || response,
          timestamp: new Date().toISOString(),
        });
      },

      logError: (endpoint, error) => {
        console.error(`[${component}] API Error:`, {
          endpoint,
          error: error.message || error,
          timestamp: new Date().toISOString(),
        });
      },
    };
  }
}

// Export logger utilities
export { APILogger };

// Initialize API logging on import
console.log("[API Logger] Initialized - All API calls will be logged");
