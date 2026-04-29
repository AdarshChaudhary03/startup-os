// API configuration and functions for the startup-os frontend

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// Helper function to make API requests
const apiRequest = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;

  const defaultOptions = {
    headers: {
      "Content-Type": "application/json",
    },
  };

  const config = { ...defaultOptions, ...options };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("API request failed:", error);
    throw error;
  }
};

// Fetch teams data
export const fetchTeams = async () => {
  try {
    const data = await apiRequest("/api/teams");
    return data;
  } catch (error) {
    console.error("Failed to fetch teams:", error);
    throw error;
  }
};

// Get orchestration plan from CEO
export const getOrchestrationPlan = async ({ task, agent_id = null }) => {
  try {
    const requestBody = {
      task,
      ...(agent_id && { agent_id }),
    };

    const data = await apiRequest("/api/orchestrate/plan", {
      method: "POST",
      body: JSON.stringify(requestBody),
    });

    return data;
  } catch (error) {
    console.error("Failed to get orchestration plan:", error);
    throw error;
  }
};

// Execute individual agent
export const executeAgent = async (
  agentId,
  { task, context = null, metadata = {} },
) => {
  try {
    const requestBody = {
      task,
      context,
      metadata,
    };

    // Convert agent_id to endpoint format (replace underscores with hyphens)
    const endpointAgentId = agentId.replace(/_/g, "-");
    const endpoint = `/api/agents/${endpointAgentId}`;

    const data = await apiRequest(endpoint, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });

    return data;
  } catch (error) {
    console.error(`Failed to execute ${agentId} agent:`, error);
    throw error;
  }
};

// Legacy orchestrate function for backward compatibility
export const orchestrate = async ({ task, agent_id = null }) => {
  try {
    const requestBody = {
      task,
      ...(agent_id && { agent_id }),
    };

    const data = await apiRequest("/api/orchestrate", {
      method: "POST",
      body: JSON.stringify(requestBody),
    });

    return data;
  } catch (error) {
    console.error("Failed to orchestrate task:", error);
    throw error;
  }
};

export default {
  fetchTeams,
  orchestrate,
  getOrchestrationPlan,
  executeAgent,
};
