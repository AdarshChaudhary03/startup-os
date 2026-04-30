import { renderHook, act } from '@testing-library/react';
import useAgentStore, { useAgentActions, useAgentStore as exportedStore } from '../agentStore';

// Mock the apiLogger to prevent actual fetch interception during tests
jest.mock('../../middleware/apiLogger', () => ({}));

describe('AgentStore Fix Tests', () => {
  beforeEach(() => {
    // Clear store state before each test
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
  });

  describe('Store Export and Access', () => {
    it('should export useAgentStore directly', () => {
      expect(exportedStore).toBeDefined();
      expect(typeof exportedStore).toBe('function');
    });

    it('should have getState method on useAgentStore', () => {
      expect(useAgentStore.getState).toBeDefined();
      expect(typeof useAgentStore.getState).toBe('function');
    });

    it('should access actions through getState', () => {
      const state = useAgentStore.getState();
      expect(state.actions).toBeDefined();
      expect(state.actions.logApiRequest).toBeDefined();
      expect(state.actions.logApiResponse).toBeDefined();
    });
  });

  describe('API Logger Integration', () => {
    it('should log API requests correctly', () => {
      const state = useAgentStore.getState();
      const requestId = state.actions.logApiRequest({
        url: '/api/test',
        method: 'POST',
        payload: { test: 'data' },
        headers: { 'Content-Type': 'application/json' },
      });

      expect(requestId).toBeDefined();
      expect(requestId).toMatch(/^req-/);

      const logs = state.actions.getApiLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].url).toBe('/api/test');
    });

    it('should log API responses correctly', () => {
      const state = useAgentStore.getState();
      const requestId = state.actions.logApiRequest({
        url: '/api/agents/content_writer',
        method: 'POST',
      });

      state.actions.logApiResponse(requestId, {
        status: 200,
        url: '/api/agents/content_writer',
        data: {
          output: 'Test content output',
          agent_id: 'content_writer',
        },
        duration: 100,
      });

      const logs = state.actions.getApiLogs();
      expect(logs).toHaveLength(2);
      expect(logs[1].type).toBe('response');
      expect(logs[1].status).toBe(200);
    });
  });

  describe('Agent Output Management', () => {
    it('should save agent output from API response', () => {
      const state = useAgentStore.getState();
      
      // Create a session first
      state.actions.createSession('test-session-123');

      // Log a response with agent output
      state.actions.logApiResponse('req-123', {
        status: 200,
        url: '/api/agents/content_writer',
        data: {
          request_id: 'req-123',
          agent_id: 'content_writer',
          agent_name: 'Content Writer',
          output: 'Generated Instagram caption with hashtags',
          timestamp: '2024-01-01T00:00:00Z',
        },
      });

      // Check if output was saved
      const output = state.actions.getAgentOutput('content_writer');
      expect(output).toBeDefined();
      expect(output.output).toBe('Generated Instagram caption with hashtags');
    });

    it('should retrieve output for cross-agent communication', () => {
      const state = useAgentStore.getState();
      
      // Create a session
      state.actions.createSession('test-session-456');

      // Save content writer output
      state.actions.saveAgentOutput('content_writer', {
        request_id: 'req-456',
        agent_id: 'content_writer',
        agent_name: 'Content Writer',
        output: 'Amazing GenAI post #AI #Tech',
        timestamp: '2024-01-01T00:00:00Z',
      });

      // Get output for social publisher
      const outputForPublisher = state.actions.getOutputForAgent(
        'social_publisher',
        'content_writer'
      );

      expect(outputForPublisher).toBeDefined();
      expect(outputForPublisher.caption).toBe('Amazing GenAI post #AI #Tech');
      expect(outputForPublisher.source).toBe('content_writer');
    });
  });

  describe('useAgentActions Hook', () => {
    it('should provide access to all actions', () => {
      const { result } = renderHook(() => useAgentActions());

      expect(result.current).toBeDefined();
      expect(result.current.createSession).toBeDefined();
      expect(result.current.saveAgentOutput).toBeDefined();
      expect(result.current.getAgentOutput).toBeDefined();
      expect(result.current.logApiRequest).toBeDefined();
      expect(result.current.logApiResponse).toBeDefined();
      expect(result.current.debugState).toBeDefined();
    });

    it('should update state through actions', () => {
      const { result } = renderHook(() => useAgentActions());

      act(() => {
        result.current.createSession('hook-test-session');
      });

      const state = useAgentStore.getState();
      expect(state.sessions.current).toBe('hook-test-session');
      expect(state.sessions.history).toContain('hook-test-session');
    });
  });
});
