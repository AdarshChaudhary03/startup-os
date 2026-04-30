import { executeAgent } from '../lib/api';
import useAgentStore from '../store/agentStore';
import agentOutputManager from '../services/agentOutputManager';

// Mock the imports
jest.mock('../store/agentStore');
jest.mock('../services/agentOutputManager');

// Mock fetch globally
global.fetch = jest.fn();

describe('executeAgent', () => {
  let mockStore;
  let mockActions;

  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();
    
    // Setup mock store structure
    mockActions = {
      createSession: jest.fn(),
      saveAgentOutput: jest.fn(),
      getAgentOutput: jest.fn(),
      getCurrentSessionOutputs: jest.fn(),
      getOutputForAgent: jest.fn(),
      logApiRequest: jest.fn(),
      logApiResponse: jest.fn(),
    };

    mockStore = {
      sessions: {
        current: 'test-session-123',
        history: ['test-session-123'],
      },
      agentOutputs: {},
      apiLogs: [],
      orchestration: {
        currentPlan: null,
        executionStatus: 'idle',
        currentStep: 0,
        totalSteps: 0,
        conversationId: null,
      },
      actions: mockActions,
    };

    // Mock the store's getState method
    useAgentStore.getState = jest.fn(() => mockStore);

    // Mock agentOutputManager
    agentOutputManager.buildAgentContext = jest.fn(() => null);
    agentOutputManager.monitorAgentExecution = jest.fn((agentId, payload, promise) => promise);

    // Mock successful API response
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        request_id: 'test-request-123',
        agent_id: 'content_writer',
        agent_name: 'Content Writer',
        output: 'Test content output',
        success: true,
      }),
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('should execute agent successfully with existing session', async () => {
    const result = await executeAgent('content_writer', {
      task: 'Write test content',
      context: 'Test context',
    });

    expect(useAgentStore.getState).toHaveBeenCalled();
    expect(mockActions.createSession).not.toHaveBeenCalled();
    expect(agentOutputManager.buildAgentContext).toHaveBeenCalledWith('content_writer', 'test-session-123');
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/agents/content_writer',
      expect.objectContaining({
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: expect.stringContaining('test-session-123'),
      })
    );
    expect(result).toEqual({
      request_id: 'test-request-123',
      agent_id: 'content_writer',
      agent_name: 'Content Writer',
      output: 'Test content output',
      success: true,
    });
  });

  test('should create new session if none exists', async () => {
    // Mock no current session
    mockStore.sessions.current = null;

    await executeAgent('content_writer', {
      task: 'Write test content',
    });

    expect(mockActions.createSession).toHaveBeenCalledWith(
      expect.stringMatching(/^session-\d+-[a-z0-9]+$/)
    );
  });

  test('should use provided sessionId over current session', async () => {
    const customSessionId = 'custom-session-456';

    await executeAgent('content_writer', {
      task: 'Write test content',
    }, customSessionId);

    expect(agentOutputManager.buildAgentContext).toHaveBeenCalledWith('content_writer', customSessionId);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        body: expect.stringContaining(customSessionId),
      })
    );
  });

  test('should handle API errors gracefully', async () => {
    // Mock API error
    global.fetch.mockResolvedValue({
      ok: false,
      statusText: 'Internal Server Error',
      json: async () => ({
        detail: 'Agent execution failed',
      }),
    });

    await expect(
      executeAgent('content_writer', { task: 'Test' })
    ).rejects.toThrow('Agent execution failed');
  });

  test('should integrate with agentOutputManager for monitoring', async () => {
    await executeAgent('social_publisher', {
      task: 'Publish content',
    });

    expect(agentOutputManager.monitorAgentExecution).toHaveBeenCalledWith(
      'social_publisher',
      expect.objectContaining({
        task: 'Publish content',
        metadata: expect.objectContaining({
          session_id: 'test-session-123',
        }),
      }),
      expect.any(Promise)
    );
  });

  test('should build context from previous agent outputs', async () => {
    const mockContext = {
      content_writer_output: 'Previous content',
      timestamp: '2025-01-27T12:00:00Z',
    };
    agentOutputManager.buildAgentContext.mockReturnValue(mockContext);

    await executeAgent('social_publisher', {
      task: 'Publish content',
    });

    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        body: expect.stringContaining(JSON.stringify(mockContext)),
      })
    );
  });
});

// Integration test for the complete flow
describe('executeAgent Integration', () => {
  test('should handle Content Writer to Social Publisher flow', async () => {
    // First execution: Content Writer
    const contentWriterResponse = {
      request_id: 'cw-123',
      agent_id: 'content_writer',
      agent_name: 'Content Writer',
      output: 'Generated Instagram caption with hashtags',
      success: true,
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => contentWriterResponse,
    });

    const contentResult = await executeAgent('content_writer', {
      task: 'Write Instagram post',
    });

    expect(contentResult).toEqual(contentWriterResponse);

    // Setup context for social publisher
    agentOutputManager.buildAgentContext.mockReturnValue({
      content_writer_output: contentWriterResponse.output,
    });

    // Second execution: Social Publisher
    const socialPublisherResponse = {
      request_id: 'sp-456',
      agent_id: 'social_publisher',
      agent_name: 'Social Media Publisher',
      output: 'Successfully published to Instagram',
      success: true,
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => socialPublisherResponse,
    });

    const publishResult = await executeAgent('social_publisher', {
      task: 'Publish to Instagram',
    });

    expect(publishResult).toEqual(socialPublisherResponse);
    expect(agentOutputManager.buildAgentContext).toHaveBeenCalledWith(
      'social_publisher',
      'test-session-123'
    );
  });
});
