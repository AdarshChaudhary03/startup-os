import { useAgentStore } from '../../store/agentStore';

// Mock fetch globally
global.fetch = jest.fn();

// Import apiLogger after setting up mocks
import '../../middleware/apiLogger';

describe('API Logger Integration Tests', () => {
  beforeEach(() => {
    // Clear store state
    useAgentStore.setState({
      sessions: { current: null, history: [] },
      agentOutputs: {},
      apiLogs: [],
      orchestration: {
        currentPlan: null,
        executionStatus: 'idle',
        currentStep: 0,
        totalSteps: 0,
        conversationId: null,
      },
    });
    
    // Reset fetch mock
    global.fetch.mockClear();
  });

  describe('Fetch Interception', () => {
    it('should intercept fetch calls and log requests', async () => {
      // Create a session
      const state = useAgentStore.getState();
      state.actions.createSession('test-session');

      // Mock fetch response
      global.fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        clone: () => ({
          json: async () => ({ success: true }),
        }),
      });

      // Make a fetch call
      await window.fetch('/api/test', {
        method: 'POST',
        body: JSON.stringify({ test: 'data' }),
        headers: { 'Content-Type': 'application/json' },
      });

      // Check if request was logged
      const logs = state.actions.getApiLogs();
      expect(logs.length).toBeGreaterThan(0);
      
      const requestLog = logs.find(log => log.type === 'request');
      expect(requestLog).toBeDefined();
      expect(requestLog.url).toBe('/api/test');
      expect(requestLog.method).toBe('POST');
    });

    it('should log Content Writer responses with output', async () => {
      const state = useAgentStore.getState();
      state.actions.createSession('content-writer-session');

      // Mock Content Writer response
      const mockResponse = {
        request_id: 'req-789',
        agent_id: 'content_writer',
        agent_name: 'Content Writer',
        output: 'Generated Instagram post about GenAI #AI #Technology',
        success: true,
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        clone: () => ({
          json: async () => mockResponse,
          text: async () => JSON.stringify(mockResponse),
        }),
      });

      // Make a fetch call to Content Writer
      await window.fetch('/api/agents/content_writer', {
        method: 'POST',
        body: JSON.stringify({ task: 'Write Instagram post' }),
      });

      // Check if response was logged and output was saved
      const logs = state.actions.getApiLogs();
      const responseLog = logs.find(log => log.type === 'response');
      expect(responseLog).toBeDefined();
      expect(responseLog.data.output).toBe(mockResponse.output);

      // Check if agent output was saved
      const agentOutput = state.actions.getAgentOutput('content_writer');
      expect(agentOutput).toBeDefined();
      expect(agentOutput.output).toBe(mockResponse.output);
    });

    it('should handle errors correctly', async () => {
      const state = useAgentStore.getState();
      state.actions.createSession('error-session');

      // Mock fetch error
      global.fetch.mockRejectedValueOnce(new Error('Network error'));

      // Make a fetch call that will fail
      await expect(
        window.fetch('/api/failing-endpoint')
      ).rejects.toThrow('Network error');

      // Check if error was logged
      const logs = state.actions.getApiLogs();
      const errorLog = logs.find(log => log.error);
      expect(errorLog).toBeDefined();
      expect(errorLog.error).toBe('Network error');
    });
  });

  describe('Special Agent Handling', () => {
    it('should log Social Media Publisher requests with context check', async () => {
      const state = useAgentStore.getState();
      state.actions.createSession('publisher-session');

      // Mock console.log to capture output
      const consoleSpy = jest.spyOn(console, 'log');

      global.fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        clone: () => ({
          json: async () => ({ success: true }),
        }),
      });

      // Make a fetch call to Social Media Publisher
      await window.fetch('/api/agents/social_publisher', {
        method: 'POST',
        body: JSON.stringify({
          task: 'Publish to Instagram',
          context: { caption: 'Test caption' },
        }),
      });

      // Check console output
      expect(consoleSpy).toHaveBeenCalledWith(
        '[API Logger] Social Media Publisher request:',
        expect.any(Object)
      );

      consoleSpy.mockRestore();
    });
  });
});
