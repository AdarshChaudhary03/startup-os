import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";

// Agent Store for managing all agent-related state
const useAgentStore = create(
  devtools(
    persist(
      immer((set, get) => ({
        // Session Management
        sessions: {
          current: null,
          history: [],
        },

        // Agent Outputs by Session
        agentOutputs: {},

        // API Logs
        apiLogs: [],

        // Orchestration State
        orchestration: {
          currentPlan: null,
          executionStatus: "idle", // idle | running | completed | failed
          currentStep: 0,
          totalSteps: 0,
          conversationId: null,
        },

        // Actions
        actions: {
          // Session Management
          createSession: (sessionId) => {
            set((state) => {
              state.sessions.current = sessionId;
              state.sessions.history.push(sessionId);
              state.agentOutputs[sessionId] = {};
            });
          },

          setCurrentSession: (sessionId) => {
            set((state) => {
              state.sessions.current = sessionId;
            });
          },

          // Save Agent Output
          saveAgentOutput: (agentId, output, sessionId = null) => {
            const session = sessionId || get().sessions.current;
            if (!session) {
              console.error(
                "[AgentStore] No active session for saving agent output",
              );
              return;
            }

            set((state) => {
              if (!state.agentOutputs[session]) {
                state.agentOutputs[session] = {};
              }

              // Extract the actual content from the output
              const extractedOutput = {
                request_id: output.request_id,
                agent_id: agentId,
                agent_name: output.agent_name,
                output: output.output, // The actual content (e.g., caption text)
                timestamp: output.timestamp || new Date().toISOString(),
                metadata: output.metadata || {},
                raw_response: output, // Store full response for debugging
              };

              state.agentOutputs[session][agentId] = extractedOutput;

              console.log(`[AgentStore] Saved output for ${agentId}:`, {
                session,
                output: extractedOutput.output?.substring(0, 100) + "...",
              });
            });
          },

          // Get Agent Output
          getAgentOutput: (agentId, sessionId = null) => {
            const session = sessionId || get().sessions.current;
            if (!session) return null;

            const outputs = get().agentOutputs[session];
            return outputs?.[agentId] || null;
          },

          // Get All Outputs for Current Session
          getCurrentSessionOutputs: () => {
            const session = get().sessions.current;
            if (!session) return {};
            return get().agentOutputs[session] || {};
          },

          // Cross-Agent Data Sharing
          getOutputForAgent: (
            targetAgentId,
            sourceAgentId,
            sessionId = null,
          ) => {
            const session = sessionId || get().sessions.current;
            if (!session) return null;

            const sourceOutput = get().agentOutputs[session]?.[sourceAgentId];
            if (!sourceOutput) {
              console.warn(
                `[AgentStore] No output found from ${sourceAgentId} for ${targetAgentId}`,
              );
              return null;
            }

            // Special handling for social_publisher getting content_writer output
            if (
              targetAgentId === "social_publisher" &&
              sourceAgentId === "content_writer"
            ) {
              return {
                caption: sourceOutput.output,
                source: sourceAgentId,
                timestamp: sourceOutput.timestamp,
              };
            }

            return sourceOutput.output;
          },

          // API Logging
          logApiRequest: (request) => {
            let requestId;
            set((state) => {
              const logEntry = {
                id: `req-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                type: "request",
                method: request.method || "GET",
                url: request.url,
                payload: request.payload,
                headers: request.headers,
                timestamp: new Date().toISOString(),
                sessionId: get().sessions.current,
              };

              state.apiLogs.push(logEntry);

              // Keep only last 100 logs to prevent memory issues
              if (state.apiLogs.length > 100) {
                state.apiLogs = state.apiLogs.slice(-100);
              }

              console.log("[API Logger] Request:", logEntry);
              requestId = logEntry.id;
            });
            return requestId;
          },

          logApiResponse: (requestId, response) => {
            set((state) => {
              const logEntry = {
                id: `res-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                requestId,
                type: "response",
                status: response.status,
                url: response.url,
                data: response.data,
                error: response.error,
                timestamp: new Date().toISOString(),
                duration: response.duration,
                sessionId: get().sessions.current,
              };

              state.apiLogs.push(logEntry);

              // Special handling for agent responses
              if (
                response.url?.includes("/api/agents/") &&
                response.data?.output
              ) {
                const agentId = response.url.split("/").pop();
                console.log(
                  `[API Logger] Agent ${agentId} response with output detected`,
                );

                // Automatically save agent output
                get().actions.saveAgentOutput(agentId, response.data);
              }

              console.log("[API Logger] Response:", {
                ...logEntry,
                data: logEntry.data?.output
                  ? {
                      ...logEntry.data,
                      output: logEntry.data.output.substring(0, 100) + "...",
                    }
                  : logEntry.data,
              });
            });
          },

          // Get API Logs
          getApiLogs: (filter = {}) => {
            const logs = get().apiLogs;
            if (!filter.type && !filter.url && !filter.sessionId) {
              return logs;
            }

            return logs.filter((log) => {
              if (filter.type && log.type !== filter.type) return false;
              if (filter.url && !log.url?.includes(filter.url)) return false;
              if (filter.sessionId && log.sessionId !== filter.sessionId)
                return false;
              return true;
            });
          },

          // Orchestration Management
          setOrchestrationPlan: (plan) => {
            set((state) => {
              state.orchestration.currentPlan = plan;
              state.orchestration.totalSteps = plan.steps?.length || 0;
              state.orchestration.currentStep = 0;
              state.orchestration.conversationId = plan.conversationId;
            });
          },

          updateOrchestrationStatus: (status) => {
            set((state) => {
              state.orchestration.executionStatus = status;
            });
          },

          incrementOrchestrationStep: () => {
            set((state) => {
              if (
                state.orchestration.currentStep < state.orchestration.totalSteps
              ) {
                state.orchestration.currentStep += 1;
              }
            });
          },

          // Clear Functions
          clearCurrentSession: () => {
            const session = get().sessions.current;
            if (session) {
              set((state) => {
                delete state.agentOutputs[session];
              });
            }
          },

          clearAllLogs: () => {
            set((state) => {
              state.apiLogs = [];
            });
          },

          // Debug Helper
          debugState: () => {
            const state = get();
            console.log("[AgentStore] Current State:", {
              currentSession: state.sessions.current,
              sessionOutputs: state.agentOutputs[state.sessions.current] || {},
              orchestration: state.orchestration,
              apiLogCount: state.apiLogs.length,
            });
          },
        },
      })),
      {
        name: "agent-store",
        partialize: (state) => ({
          sessions: state.sessions,
          agentOutputs: state.agentOutputs,
          orchestration: state.orchestration,
        }),
      },
    ),
    {
      name: "AgentStore",
    },
  ),
);

// Export actions separately for easier access
export const useAgentActions = () => useAgentStore((state) => state.actions);

// Export the store itself for direct access when needed
export { useAgentStore };

// Export selectors
export const useCurrentSession = () =>
  useAgentStore((state) => state.sessions.current);
export const useAgentOutput = (agentId) => {
  const actions = useAgentActions();
  return actions.getAgentOutput(agentId);
};
export const useApiLogs = (filter) => {
  const actions = useAgentActions();
  return actions.getApiLogs(filter);
};
export const useOrchestrationState = () =>
  useAgentStore((state) => state.orchestration);

export default useAgentStore;
