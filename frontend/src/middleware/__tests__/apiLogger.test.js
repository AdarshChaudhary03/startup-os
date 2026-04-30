import { APILogger } from '../apiLogger';
import { renderHook } from '@testing-library/react';
import { useAgentActions } from '../../store/agentStore';

// Mock the store
jest.mock('../../store/agentStore', () => ({
  useAgentActions: {
    getState: jest.fn(() => ({
      logApiRequest: jest.fn().mockReturnValue('req-123'),
      logApiResponse: jest.fn(),
      saveAgentOutput: jest.fn(),
      sessions: { current: 'test-session' },
    })),
  },
}));

// Store the original fetch
const originalFetch = global.fetch;

describe('API Logger', () => {
  let mockFetch;
  let consoleLogSpy;
  let consoleErrorSpy;

  beforeEach(() => {
    // Reset fetch mock
    mockFetch = jest.fn();
    global.fetch = mockFetch;
    
    // Spy on console methods
    consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
    
    // Clear mock calls
    jest.clearAllMocks();
  });

  afterEach(() => {
    // Restore console methods
    consoleLogSpy.mockRestore();
    consoleErrorSpy.mockRestore();
  });

  afterAll(() => {
    // Restore original fetch
    global.fetch = originalFetch;
  });

  describe('Fetch Interception', () => {
    test('should log API requests', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        clone: () => mockResponse,
        json: async () => ({ success: true }),
      };
      mockFetch.mockResolvedValue(mockResponse);

      const agentActions = useAgentActions.getState();

      await fetch('/api/test', {
        method: 'POST',
        body: JSON.stringify({ data: 'test' }),
      });

      expect(agentActions.logApiRequest).toHaveBeenCalledWith({
        url: '/api/test',
        method: 'POST',
        payload: { data: 'test' },
        headers: {},
      });
    });

    test('should log API responses', async () => {
      const responseData = { output: 'test output' };
      const mockResponse = {
        ok: true,
        status: 200,
        clone: () => mockResponse,
        json: async () => responseData,
      };
      mockFetch.mockResolvedValue(mockResponse);

      const agentActions = useAgentActions.getState();

      await fetch('/api/test');

      expect(agentActions.logApiResponse).toHaveBeenCalledWith('req-123', {
        status: 200,
        url: '/api/test',
        data: responseData,
        duration: expect.any(Number),
        error: null,
      });
    });

    test('should handle Content Writer responses specially', async () => {
      const contentWriterOutput = {
        output: 'Generated Instagram post content with hashtags #AI #Tech',
        request_id: 'req-456',
      };
      const mockResponse = {
        ok: true,
        status: 200,
        clone: () => mockResponse,
        json: async () => contentWriterOutput,
      };
      mockFetch.mockResolvedValue(mockResponse);

      await fetch('/api/agents/content_writer', {
        method: 'POST',
        body: JSON.stringify({ task: 'Write Instagram post' }),
      });

      expect(consoleLogSpy).toHaveBeenCalledWith(
        '[API Logger] Content Writer output detected:'
      );
      expect(consoleLogSpy).toHaveBeenCalledWith(
        '- Output length:',
        contentWriterOutput.output.length
      );
    });

    test('should log Social Media Publisher requests', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        clone: () => mockResponse,
        json: async () => ({ success: true }),
      };
      mockFetch.mockResolvedValue(mockResponse);

      const payload = {
        task: 'Publish to Instagram',
        context: { content_writer_output: 'Caption text' },
      };

      await fetch('/api/agents/social_publisher', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      expect(consoleLogSpy).toHaveBeenCalledWith(
        '[API Logger] Social Media Publisher request:'
      );
      expect(consoleLogSpy).toHaveBeenCalledWith('- Task:', payload.task);
      expect(consoleLogSpy).toHaveBeenCalledWith('- Context:', payload.context);
    });

    test('should handle API errors', async () => {
      const error = new Error('Network error');
      mockFetch.mockRejectedValue(error);

      const agentActions = useAgentActions.getState();

      await expect(fetch('/api/test')).rejects.toThrow('Network error');

      expect(agentActions.logApiResponse).toHaveBeenCalledWith('req-123', {
        status: 0,
        url: '/api/test',
        error: 'Network error',
        duration: expect.any(Number),
      });
    });
  });

  describe('APILogger Utility Class', () => {
    test('should log agent interactions', () => {
      APILogger.logAgentInteraction('content_writer', 'social_publisher', {
        caption: 'Test caption',
      });

      expect(consoleLogSpy).toHaveBeenCalledWith(
        '[Agent Interaction] content_writer → social_publisher:',
        expect.objectContaining({
          timestamp: expect.any(String),
          data: { caption: 'Test caption' },
        })
      );
    });

    test('should truncate long string data in agent interactions', () => {
      const longString = 'a'.repeat(200);
      APILogger.logAgentInteraction('agent1', 'agent2', longString);

      expect(consoleLogSpy).toHaveBeenCalledWith(
        '[Agent Interaction] agent1 → agent2:',
        expect.objectContaining({
          data: 'a'.repeat(100) + '...',
        })
      );
    });

    test('should log orchestration steps', () => {
      APILogger.logOrchestrationStep(1, 3, 'content_writer', 'Write content');

      expect(consoleLogSpy).toHaveBeenCalledWith(
        '[Orchestration] Step 1/3:',
        expect.objectContaining({
          agent: 'content_writer',
          instruction: 'Write content',
          timestamp: expect.any(String),
        })
      );
    });

    test('should log state updates', () => {
      APILogger.logStateUpdate('AGENT_OUTPUT_SAVED', {
        agent: 'content_writer',
        outputLength: 500,
      });

      expect(consoleLogSpy).toHaveBeenCalledWith(
        '[State Update] AGENT_OUTPUT_SAVED:',
        expect.objectContaining({
          timestamp: expect.any(String),
          data: {
            agent: 'content_writer',
            outputLength: 500,
          },
        })
      );
    });

    test('should create request logger for components', () => {
      const logger = APILogger.createRequestLogger('Dashboard');

      logger.logRequest('/api/agents/content_writer', { task: 'Write post' });
      expect(consoleLogSpy).toHaveBeenCalledWith(
        '[Dashboard] API Request:',
        expect.objectContaining({
          endpoint: '/api/agents/content_writer',
          payload: { task: 'Write post' },
        })
      );

      logger.logResponse('/api/agents/content_writer', { status: 200 }, 1500);
      expect(consoleLogSpy).toHaveBeenCalledWith(
        '[Dashboard] API Response:',
        expect.objectContaining({
          endpoint: '/api/agents/content_writer',
          status: 200,
          duration: '1500ms',
        })
      );

      logger.logError('/api/agents/content_writer', new Error('Test error'));
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[Dashboard] API Error:',
        expect.objectContaining({
          endpoint: '/api/agents/content_writer',
          error: 'Test error',
        })
      );
    });
  });

  describe('Agent Output Auto-Save', () => {
    test('should auto-save agent outputs from responses', async () => {
      const agentOutput = {
        output: 'Generated content',
        request_id: 'req-789',
        agent_name: 'Content Writer',
      };
      const mockResponse = {
        ok: true,
        status: 200,
        clone: () => mockResponse,
        json: async () => agentOutput,
      };
      mockFetch.mockResolvedValue(mockResponse);

      const agentActions = useAgentActions.getState();

      await fetch('/api/agents/content_writer', {
        method: 'POST',
        body: JSON.stringify({ task: 'Write content' }),
      });

      // Verify auto-save was triggered
      expect(consoleLogSpy).toHaveBeenCalledWith(
        '[API Logger] Agent content_writer response with output detected'
      );
      expect(agentActions.saveAgentOutput).toHaveBeenCalledWith(
        'content_writer',
        agentOutput
      );
    });
  });
});