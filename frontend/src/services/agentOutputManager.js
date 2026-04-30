// Agent Output Manager - Handles extraction and management of agent outputs
import { useAgentStore } from "../store/agentStore";
import { APILogger } from "../middleware/apiLogger";

class AgentOutputManager {
  constructor() {
    this.logger = APILogger.createRequestLogger("AgentOutputManager");
  }

  /**
   * Extract and save Content Writer output
   * @param {Object} response - The API response from content_writer endpoint
   * @param {string} sessionId - Current session ID
   */
  extractContentWriterOutput(response, sessionId) {
    if (!response || !response.output) {
      console.error(
        "[AgentOutputManager] No output found in Content Writer response",
      );
      return null;
    }

    const store = useAgentStore.getState();
    const agentActions = store.actions;

    // Log the extraction
    console.log("[AgentOutputManager] Extracting Content Writer output:");
    console.log("- Session ID:", sessionId);
    console.log("- Output length:", response.output.length);
    console.log("- Output preview:", response.output.substring(0, 200) + "...");

    // Save to state store
    const { actions: saveActions } = useAgentStore.getState();
    saveActions.saveAgentOutput("content_writer", response, sessionId);

    // Return the extracted output for immediate use
    return {
      content: response.output,
      metadata: {
        request_id: response.request_id,
        timestamp: response.timestamp,
        agent_name: response.agent_name || "Content Writer",
      },
    };
  }

  /**
   * Prepare data for Social Media Publisher
   * @param {string} sessionId - Current session ID
   * @returns {Object} Formatted data for social media publisher
   */
  prepareDataForSocialPublisher(sessionId) {
    // Get Content Writer output from state
    const store = useAgentStore.getState();
    const contentWriterOutput = store.actions.getAgentOutput(
      "content_writer",
      sessionId,
    );

    if (!contentWriterOutput) {
      console.warn(
        "[AgentOutputManager] No Content Writer output found for Social Publisher",
      );
      return null;
    }

    console.log("[AgentOutputManager] Preparing data for Social Publisher:");
    console.log(
      "- Content Writer output found:",
      contentWriterOutput.output?.substring(0, 100) + "...",
    );

    // Format data for Social Publisher
    const socialPublisherData = {
      caption: contentWriterOutput.output,
      source: "content_writer",
      source_request_id: contentWriterOutput.request_id,
      metadata: {
        content_generated_at: contentWriterOutput.timestamp,
        session_id: sessionId,
      },
    };

    APILogger.logAgentInteraction(
      "content_writer",
      "social_publisher",
      socialPublisherData,
    );

    return socialPublisherData;
  }

  /**
   * Build context for agent execution with previous outputs
   * @param {string} targetAgentId - The agent that will receive the context
   * @param {string} sessionId - Current session ID
   * @returns {Object} Context object with previous agent outputs
   */
  buildAgentContext(targetAgentId, sessionId) {
    const store = useAgentStore.getState();

    // Special handling for social_publisher
    if (
      targetAgentId === "social_publisher" ||
      targetAgentId === "social-media-publisher"
    ) {
      const contentData = this.prepareDataForSocialPublisher(sessionId);
      if (contentData) {
        return {
          content_writer_output: contentData.caption,
          caption: contentData.caption,
          metadata: contentData.metadata,
        };
      }
    }

    // Generic context building for other agents
    const allOutputs = store.actions.getCurrentSessionOutputs();
    const context = {};

    Object.entries(allOutputs).forEach(([agentId, output]) => {
      if (agentId !== targetAgentId) {
        context[`${agentId}_output`] = output.output;
      }
    });

    return context;
  }

  /**
   * Monitor agent execution and capture outputs
   * @param {string} agentId - The agent being executed
   * @param {Object} payload - The request payload
   * @param {Promise} executionPromise - The promise of agent execution
   * @returns {Promise} Enhanced promise with output capture
   */
  async monitorAgentExecution(agentId, payload, executionPromise) {
    const startTime = Date.now();
    const sessionId =
      payload.metadata?.session_id || useAgentStore.getState().sessions.current;

    console.log(`[AgentOutputManager] Monitoring ${agentId} execution:`);
    console.log("- Session ID:", sessionId);
    console.log("- Task:", payload.task);

    try {
      const response = await executionPromise;
      const duration = Date.now() - startTime;

      // Log successful execution
      this.logger.logResponse(`/api/agents/${agentId}`, response, duration);

      // Special handling for content_writer
      if (agentId === "content_writer" && response.output) {
        this.extractContentWriterOutput(response, sessionId);
      }

      // Save any agent output to state
      if (response.output) {
        const { actions } = useAgentStore.getState();
        actions.saveAgentOutput(agentId, response, sessionId);
      }

      return response;
    } catch (error) {
      this.logger.logError(`/api/agents/${agentId}`, error);
      throw error;
    }
  }

  /**
   * Get formatted output history for debugging
   * @param {string} sessionId - Current session ID
   * @returns {Array} Formatted output history
   */
  getOutputHistory(sessionId) {
    const { actions } = useAgentStore.getState();
    const outputs = actions.getCurrentSessionOutputs();

    return Object.entries(outputs).map(([agentId, output]) => ({
      agent: agentId,
      timestamp: output.timestamp,
      outputPreview: output.output?.substring(0, 100) + "...",
      requestId: output.request_id,
    }));
  }

  /**
   * Clear outputs for a specific session
   * @param {string} sessionId - Session ID to clear
   */
  clearSessionOutputs(sessionId) {
    const { actions } = useAgentStore.getState();
    actions.clearCurrentSession();
    console.log(
      `[AgentOutputManager] Cleared outputs for session: ${sessionId}`,
    );
  }
}

// Create singleton instance
const agentOutputManager = new AgentOutputManager();

export default agentOutputManager;
