import agentOutputManager from '../agentOutputManager';
import { useAgentStore } from '../../store/agentStore';

// Mock the store
jest.mock('../../store/agentStore', () => ({
  useAgentStore: jest.fn()
}));

// Mock the API Logger
jest.mock('../../middleware/apiLogger', () => ({
  APILogger: {
    createRequestLogger: jest.fn(() => ({
      logResponse: jest.fn(),
      logError: jest.fn()
    })),
    logAgentInteraction: jest.fn()
  }
}));

describe('AgentOutputManager', () => {
  let mockStore;
  let mockActions;

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Setup mock actions
    mockActions = {
      getCurrentSessionOutputs: jest.fn(),
      getAgentOutput: jest.fn(),
      saveAgentOutput: jest.fn(),
      clearCurrentSession: jest.fn()
    };
    
    // Setup mock store
    mockStore = {
      sessions: {
        current: 'test-session-123'
      },
      actions: mockActions
    };
    
    // Configure the mock to return our store
    useAgentStore.getState = jest.fn(() => mockStore);
  });

  describe('extractContentWriterOutput', () => {
    it('should extract and save content writer output', () => {
      const response = {
        request_id: 'req-123',
        agent_name: 'Content Writer',
        output: 'Instagram post about GenAI for IT professionals',
        timestamp: '2025-01-27T10:00:00Z'
      };
      const sessionId = 'test-session';
      
      const result = agentOutputManager.extractContentWriterOutput(response, sessionId);
      
      expect(mockActions.saveAgentOutput).toHaveBeenCalledWith(
        'content_writer',
        response,
        sessionId
      );
      
      expect(result).toEqual({
        content: response.output,
        metadata: {
          request_id: response.request_id,
          timestamp: response.timestamp,
          agent_name: response.agent_name
        }
      });
    });

    it('should return null when no output in response', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      const response = { request_id: 'req-123' }; // No output field
      
      const result = agentOutputManager.extractContentWriterOutput(response, 'session-123');
      
      expect(result).toBeNull();
      expect(consoleSpy).toHaveBeenCalledWith(
        '[AgentOutputManager] No output found in Content Writer response'
      );
      
      consoleSpy.mockRestore();
    });

    it('should handle null response gracefully', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      const result = agentOutputManager.extractContentWriterOutput(null, 'session-123');
      
      expect(result).toBeNull();
      expect(consoleSpy).toHaveBeenCalledWith(
        '[AgentOutputManager] No output found in Content Writer response'
      );
      
      consoleSpy.mockRestore();
    });
  });

  describe('prepareDataForSocialPublisher', () => {
    it('should prepare data from content writer output', () => {
      const contentWriterOutput = {
        request_id: 'req-123',
        output: '🚀 Upskill with GenAI 🤖 Learn the latest in AI #GenAI #Tech',
        timestamp: '2025-01-27T10:00:00Z'
      };
      
      mockActions.getAgentOutput.mockReturnValue(contentWriterOutput);
      
      const result = agentOutputManager.prepareDataForSocialPublisher('test-session');
      
      expect(mockActions.getAgentOutput).toHaveBeenCalledWith('content_writer', 'test-session');
      expect(result).toEqual({
        caption: contentWriterOutput.output,
        source: 'content_writer',
        source_request_id: contentWriterOutput.request_id,
        metadata: {
          content_generated_at: contentWriterOutput.timestamp,
          session_id: 'test-session'
        }
      });
    });

    it('should return null when no content writer output found', () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      mockActions.getAgentOutput.mockReturnValue(null);
      
      const result = agentOutputManager.prepareDataForSocialPublisher('test-session');
      
      expect(result).toBeNull();
      expect(consoleSpy).toHaveBeenCalledWith(
        '[AgentOutputManager] No Content Writer output found for Social Publisher'
      );
      
      consoleSpy.mockRestore();
    });
  });

  describe('buildAgentContext', () => {
    it('should build context for social publisher with content writer output', () => {
      const contentData = {
        caption: 'Test Instagram caption',
        metadata: { session_id: 'test-session' }
      };
      
      // Mock prepareDataForSocialPublisher
      jest.spyOn(agentOutputManager, 'prepareDataForSocialPublisher')
        .mockReturnValue(contentData);
      
      const context = agentOutputManager.buildAgentContext('social_publisher', 'test-session');
      
      expect(context).toEqual({
        content_writer_output: contentData.caption,
        caption: contentData.caption,
        metadata: contentData.metadata
      });
    });

    it('should handle social-media-publisher alias', () => {
      const contentData = {
        caption: 'Test Instagram caption',
        metadata: { session_id: 'test-session' }
      };
      
      jest.spyOn(agentOutputManager, 'prepareDataForSocialPublisher')
        .mockReturnValue(contentData);
      
      const context = agentOutputManager.buildAgentContext('social-media-publisher', 'test-session');
      
      expect(context).toEqual({
        content_writer_output: contentData.caption,
        caption: contentData.caption,
        metadata: contentData.metadata
      });
    });

    it('should build generic context for other agents', () => {
      const allOutputs = {
        content_writer: { output: 'Content output' },
        analyzer: { output: 'Analysis output' }
      };
      
      mockActions.getCurrentSessionOutputs.mockReturnValue(allOutputs);
      
      const context = agentOutputManager.buildAgentContext('reporter', 'test-session');
      
      expect(context).toEqual({
        content_writer_output: 'Content output',
        analyzer_output: 'Analysis output'
      });
    });

    it('should exclude target agent from context', () => {
      const allOutputs = {
        content_writer: { output: 'Content output' },
        reporter: { output: 'Reporter output' }
      };
      
      mockActions.getCurrentSessionOutputs.mockReturnValue(allOutputs);
      
      const context = agentOutputManager.buildAgentContext('reporter', 'test-session');
      
      expect(context).toEqual({
        content_writer_output: 'Content output'
      });
      expect(context).not.toHaveProperty('reporter_output');
    });
  });

  describe('monitorAgentExecution', () => {
    it('should monitor successful agent execution and save output', async () => {
      const agentId = 'content_writer';
      const payload = {
        task: 'Write Instagram post',
        metadata: { session_id: 'test-session' }
      };
      const response = {
        request_id: 'req-123',
        output: 'Instagram post content',
        timestamp: '2025-01-27T10:00:00Z'
      };
      
      const executionPromise = Promise.resolve(response);
      
      const result = await agentOutputManager.monitorAgentExecution(
        agentId,
        payload,
        executionPromise
      );
      
      expect(result).toEqual(response);
      expect(mockActions.saveAgentOutput).toHaveBeenCalledWith(
        agentId,
        response,
        'test-session'
      );
    });

    it('should extract content writer output specifically', async () => {
      const agentId = 'content_writer';
      const payload = { task: 'Write post' };
      const response = {
        output: 'Content writer output',
        request_id: 'req-123'
      };
      
      jest.spyOn(agentOutputManager, 'extractContentWriterOutput');
      
      await agentOutputManager.monitorAgentExecution(
        agentId,
        payload,
        Promise.resolve(response)
      );
      
      expect(agentOutputManager.extractContentWriterOutput).toHaveBeenCalledWith(
        response,
        'test-session-123'
      );
    });

    it('should handle execution errors', async () => {
      const agentId = 'content_writer';
      const payload = { task: 'Write post' };
      const error = new Error('API Error');
      
      const executionPromise = Promise.reject(error);
      
      await expect(
        agentOutputManager.monitorAgentExecution(agentId, payload, executionPromise)
      ).rejects.toThrow('API Error');
    });

    it('should use session from payload metadata if provided', async () => {
      const agentId = 'content_writer';
      const payload = {
        task: 'Write post',
        metadata: { session_id: 'custom-session-456' }
      };
      const response = { output: 'Test output' };
      
      await agentOutputManager.monitorAgentExecution(
        agentId,
        payload,
        Promise.resolve(response)
      );
      
      expect(mockActions.saveAgentOutput).toHaveBeenCalledWith(
        agentId,
        response,
        'custom-session-456'
      );
    });
  });

  describe('getOutputHistory', () => {
    it('should return formatted output history', () => {
      const outputs = {
        content_writer: {
          output: 'Long content writer output that should be truncated...',
          timestamp: '2025-01-27T10:00:00Z',
          request_id: 'req-123'
        },
        social_publisher: {
          output: 'Published successfully',
          timestamp: '2025-01-27T10:05:00Z',
          request_id: 'req-456'
        }
      };
      
      mockActions.getCurrentSessionOutputs.mockReturnValue(outputs);
      
      const history = agentOutputManager.getOutputHistory('test-session');
      
      expect(history).toHaveLength(2);
      expect(history[0]).toEqual({
        agent: 'content_writer',
        timestamp: outputs.content_writer.timestamp,
        outputPreview: outputs.content_writer.output + '...',
        requestId: outputs.content_writer.request_id
      });
    });

    it('should handle empty outputs', () => {
      mockActions.getCurrentSessionOutputs.mockReturnValue({});
      
      const history = agentOutputManager.getOutputHistory('test-session');
      
      expect(history).toEqual([]);
    });
  });

  describe('clearSessionOutputs', () => {
    it('should clear outputs for session', () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
      
      agentOutputManager.clearSessionOutputs('test-session-123');
      
      expect(mockActions.clearCurrentSession).toHaveBeenCalled();
      expect(consoleSpy).toHaveBeenCalledWith(
        '[AgentOutputManager] Cleared outputs for session: test-session-123'
      );
      
      consoleSpy.mockRestore();
    });
  });
});