import { renderHook, act } from "@testing-library/react";
import { useAgentStore, useAgentActions } from "../agentStore";

describe("AgentStore State Management", () => {
  beforeEach(() => {
    // Clear the store before each test
    const { result } = renderHook(() => useAgentStore());
    act(() => {
      result.current.actions.clearAllLogs();
      result.current.actions.clearCurrentSession();
    });
  });

  describe("getCurrentSessionOutputs", () => {
    it("should return empty object when no session is active", () => {
      const { result } = renderHook(() => useAgentActions());

      const outputs = result.current.getCurrentSessionOutputs();
      expect(outputs).toEqual({});
    });

    it("should return all outputs for current session", () => {
      const { result } = renderHook(() => useAgentActions());

      act(() => {
        // Create a session
        result.current.createSession("test-session-123");

        // Save some agent outputs
        result.current.saveAgentOutput("content_writer", {
          request_id: "req-123",
          agent_name: "Content Writer",
          output: "Test content for Instagram post",
          timestamp: "2025-01-27T10:00:00Z",
        });

        result.current.saveAgentOutput("social_publisher", {
          request_id: "req-456",
          agent_name: "Social Media Publisher",
          output: "Published successfully",
          timestamp: "2025-01-27T10:05:00Z",
        });
      });

      const outputs = result.current.getCurrentSessionOutputs();

      expect(Object.keys(outputs)).toHaveLength(2);
      expect(outputs.content_writer).toBeDefined();
      expect(outputs.content_writer.output).toBe(
        "Test content for Instagram post",
      );
      expect(outputs.social_publisher).toBeDefined();
      expect(outputs.social_publisher.output).toBe("Published successfully");
    });

    it("should return outputs only for current session", () => {
      const { result } = renderHook(() => useAgentActions());

      act(() => {
        // Create first session and add output
        result.current.createSession("session-1");
        result.current.saveAgentOutput("content_writer", {
          output: "Session 1 content",
        });

        // Create second session and add output
        result.current.createSession("session-2");
        result.current.saveAgentOutput("content_writer", {
          output: "Session 2 content",
        });
      });

      const outputs = result.current.getCurrentSessionOutputs();

      expect(Object.keys(outputs)).toHaveLength(1);
      expect(outputs.content_writer.output).toBe("Session 2 content");
    });
  });

  describe("getAgentOutput", () => {
    it("should return null when no session is active", () => {
      const { result } = renderHook(() => useAgentActions());

      const output = result.current.getAgentOutput("content_writer");
      expect(output).toBeNull();
    });

    it("should return null when agent has no output", () => {
      const { result } = renderHook(() => useAgentActions());

      act(() => {
        result.current.createSession("test-session");
      });

      const output = result.current.getAgentOutput("content_writer");
      expect(output).toBeNull();
    });

    it("should return specific agent output", () => {
      const { result } = renderHook(() => useAgentActions());

      act(() => {
        result.current.createSession("test-session");
        result.current.saveAgentOutput("content_writer", {
          request_id: "req-123",
          agent_name: "Content Writer",
          output: "Instagram post about GenAI",
          timestamp: "2025-01-27T10:00:00Z",
        });
      });

      const output = result.current.getAgentOutput("content_writer");

      expect(output).toBeDefined();
      expect(output.output).toBe("Instagram post about GenAI");
      expect(output.request_id).toBe("req-123");
    });

    it("should return output for specific session when provided", () => {
      const { result } = renderHook(() => useAgentActions());

      act(() => {
        // Create two sessions with different outputs
        result.current.createSession("session-1");
        result.current.saveAgentOutput("content_writer", {
          output: "Session 1 content",
        });

        result.current.createSession("session-2");
        result.current.saveAgentOutput("content_writer", {
          output: "Session 2 content",
        });
      });

      // Get output from session-1 specifically
      const output = result.current.getAgentOutput(
        "content_writer",
        "session-1",
      );

      expect(output.output).toBe("Session 1 content");
    });
  });

  describe("saveAgentOutput", () => {
    it("should save agent output with extracted fields", () => {
      const { result } = renderHook(() => useAgentActions());

      act(() => {
        result.current.createSession("test-session");
        result.current.saveAgentOutput("content_writer", {
          request_id: "req-789",
          agent_name: "Content Writer",
          output: "🚀 Upskill with GenAI 🤖 Learn the latest in AI...",
          timestamp: "2025-01-27T10:00:00Z",
          metadata: { word_count: 100 },
        });
      });

      const output = result.current.getAgentOutput("content_writer");

      expect(output.request_id).toBe("req-789");
      expect(output.agent_id).toBe("content_writer");
      expect(output.agent_name).toBe("Content Writer");
      expect(output.output).toContain("Upskill with GenAI");
      expect(output.metadata.word_count).toBe(100);
      expect(output.raw_response).toBeDefined();
    });

    it("should handle missing session gracefully", () => {
      const { result } = renderHook(() => useAgentActions());
      const consoleSpy = jest.spyOn(console, "error").mockImplementation();

      act(() => {
        result.current.saveAgentOutput("content_writer", {
          output: "Test content",
        });
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        "[AgentStore] No active session for saving agent output",
      );

      consoleSpy.mockRestore();
    });
  });

  describe("getOutputForAgent", () => {
    it("should return formatted output for social_publisher from content_writer", () => {
      const { result } = renderHook(() => useAgentActions());

      act(() => {
        result.current.createSession("test-session");
        result.current.saveAgentOutput("content_writer", {
          output: "Amazing GenAI content with hashtags #AI #Tech",
          timestamp: "2025-01-27T10:00:00Z",
        });
      });

      const output = result.current.getOutputForAgent(
        "social_publisher",
        "content_writer",
      );

      expect(output).toBeDefined();
      expect(output.caption).toBe(
        "Amazing GenAI content with hashtags #AI #Tech",
      );
      expect(output.source).toBe("content_writer");
      expect(output.timestamp).toBe("2025-01-27T10:00:00Z");
    });

    it("should return raw output for other agent combinations", () => {
      const { result } = renderHook(() => useAgentActions());

      act(() => {
        result.current.createSession("test-session");
        result.current.saveAgentOutput("analyzer", {
          output: "Analysis complete",
          timestamp: "2025-01-27T10:00:00Z",
        });
      });

      const output = result.current.getOutputForAgent("reporter", "analyzer");

      expect(output).toBe("Analysis complete");
    });

    it("should return null when source agent has no output", () => {
      const { result } = renderHook(() => useAgentActions());
      const consoleSpy = jest.spyOn(console, "warn").mockImplementation();

      act(() => {
        result.current.createSession("test-session");
      });

      const output = result.current.getOutputForAgent(
        "social_publisher",
        "content_writer",
      );

      expect(output).toBeNull();
      expect(consoleSpy).toHaveBeenCalledWith(
        "[AgentStore] No output found from content_writer for social_publisher",
      );

      consoleSpy.mockRestore();
    });
  });

  describe("Session Management", () => {
    it("should create new session and set as current", () => {
      const { result: storeResult } = renderHook(() => useAgentStore());
      const { result: actionsResult } = renderHook(() => useAgentActions());

      act(() => {
        actionsResult.current.createSession("new-session-123");
      });

      expect(storeResult.current.sessions.current).toBe("new-session-123");
      expect(storeResult.current.sessions.history).toContain("new-session-123");
      expect(storeResult.current.agentOutputs["new-session-123"]).toEqual({});
    });

    it("should clear current session outputs", () => {
      const { result } = renderHook(() => useAgentActions());

      act(() => {
        result.current.createSession("test-session");
        result.current.saveAgentOutput("content_writer", {
          output: "Test content",
        });
      });

      expect(result.current.getCurrentSessionOutputs()).toHaveProperty(
        "content_writer",
      );

      act(() => {
        result.current.clearCurrentSession();
      });

      expect(result.current.getCurrentSessionOutputs()).toEqual({});
    });
  });
});
