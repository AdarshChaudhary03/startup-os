import { renderHook, act, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { useCEOChat } from '../useCEOChat';
import * as api from '../../lib/api';

// Mock the API module
vi.mock('../../lib/api');

describe('useCEOChat', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initializes with default state', () => {
    const { result } = renderHook(() => useCEOChat());

    expect(result.current.conversationId).toBeNull();
    expect(result.current.messages).toEqual([]);
    expect(result.current.conversationState).toBe('idle');
    expect(result.current.requirements).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.isActive).toBe(false);
    expect(result.current.canSendMessage).toBe(false);
    expect(result.current.isComplete).toBe(false);
  });

  it('starts a conversation successfully', async () => {
    const mockResponse = {
      conversation_id: 'test-123',
      state: 'gathering_requirements',
      message: 'What would you like to build?',
      requirements: null,
    };

    api.startCEOChat.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useCEOChat());

    await act(async () => {
      await result.current.startConversation('Build a feature');
    });

    expect(api.startCEOChat).toHaveBeenCalledWith('Build a feature');
    expect(result.current.conversationId).toBe('test-123');
    expect(result.current.conversationState).toBe('gathering_requirements');
    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0]).toMatchObject({
      type: 'user',
      content: 'Build a feature',
    });
    expect(result.current.messages[1]).toMatchObject({
      type: 'ceo',
      content: mockResponse.message,
    });
    expect(result.current.isActive).toBe(true);
    expect(result.current.canSendMessage).toBe(true);
  });

  it('handles start conversation error', async () => {
    const errorMessage = 'Network error';
    api.startCEOChat.mockRejectedValueOnce(new Error(errorMessage));

    const { result } = renderHook(() => useCEOChat());

    await act(async () => {
      try {
        await result.current.startConversation('Build a feature');
      } catch (error) {
        // Expected error
      }
    });

    expect(result.current.error).toBe(errorMessage);
    expect(result.current.conversationId).toBeNull();
    expect(result.current.messages).toEqual([]);
  });

  it('sends a message in active conversation', async () => {
    const startResponse = {
      conversation_id: 'test-123',
      state: 'gathering_requirements',
      message: 'What is your target audience?',
    };

    const sendResponse = {
      state: 'gathering_requirements',
      message: 'What features do you need?',
      requirements: {
        target_audience: 'Developers',
      },
    };

    api.startCEOChat.mockResolvedValueOnce(startResponse);
    api.sendCEOChatMessage.mockResolvedValueOnce(sendResponse);

    const { result } = renderHook(() => useCEOChat());

    // Start conversation first
    await act(async () => {
      await result.current.startConversation('Build a dashboard');
    });

    // Send a message
    await act(async () => {
      await result.current.sendMessage('For developers');
    });

    expect(api.sendCEOChatMessage).toHaveBeenCalledWith('test-123', 'For developers');
    expect(result.current.messages).toHaveLength(4); // 2 from start + 2 from send
    expect(result.current.messages[2]).toMatchObject({
      type: 'user',
      content: 'For developers',
    });
    expect(result.current.messages[3]).toMatchObject({
      type: 'ceo',
      content: sendResponse.message,
    });
    expect(result.current.requirements).toEqual(sendResponse.requirements);
  });

  it('throws error when sending message without active conversation', async () => {
    const { result } = renderHook(() => useCEOChat());

    await expect(async () => {
      await act(async () => {
        await result.current.sendMessage('Test message');
      });
    }).rejects.toThrow('No active conversation');
  });

  it('removes user message on send error', async () => {
    const startResponse = {
      conversation_id: 'test-123',
      state: 'gathering_requirements',
      message: 'What do you need?',
    };

    api.startCEOChat.mockResolvedValueOnce(startResponse);
    api.sendCEOChatMessage.mockRejectedValueOnce(new Error('Send failed'));

    const { result } = renderHook(() => useCEOChat());

    // Start conversation
    await act(async () => {
      await result.current.startConversation('Build something');
    });

    const initialMessageCount = result.current.messages.length;

    // Try to send a message that will fail
    await act(async () => {
      try {
        await result.current.sendMessage('This will fail');
      } catch (error) {
        // Expected error
      }
    });

    // Message count should remain the same (user message was removed)
    expect(result.current.messages).toHaveLength(initialMessageCount);
    expect(result.current.error).toBe('Send failed');
  });

  it('gets conversation state', async () => {
    const startResponse = {
      conversation_id: 'test-123',
      state: 'gathering_requirements',
      message: 'Initial message',
    };

    const stateResponse = {
      state: 'requirements_complete',
      requirements: {
        purpose: 'Dashboard',
        target_audience: 'Developers',
      },
    };

    api.startCEOChat.mockResolvedValueOnce(startResponse);
    api.getCEOChatState.mockResolvedValueOnce(stateResponse);

    const { result } = renderHook(() => useCEOChat());

    // Start conversation
    await act(async () => {
      await result.current.startConversation('Build dashboard');
    });

    // Get state
    await act(async () => {
      await result.current.getState();
    });

    expect(api.getCEOChatState).toHaveBeenCalledWith('test-123');
    expect(result.current.conversationState).toBe('requirements_complete');
    expect(result.current.requirements).toEqual(stateResponse.requirements);
    expect(result.current.isComplete).toBe(true);
  });

  it('finalizes requirements', async () => {
    const startResponse = {
      conversation_id: 'test-123',
      state: 'requirements_complete',
      message: 'Ready to finalize',
    };

    const finalizeResponse = {
      requirements: {
        purpose: 'E-commerce',
        target_audience: 'Small businesses',
        key_features: ['Catalog', 'Cart', 'Payment'],
      },
      plan: {
        mode: 'multi_agent',
        steps: [{ agent_id: 'frontend', instruction: 'Build UI' }],
      },
    };

    api.startCEOChat.mockResolvedValueOnce(startResponse);
    api.finalizeCEORequirements.mockResolvedValueOnce(finalizeResponse);

    const { result } = renderHook(() => useCEOChat());

    // Start conversation
    await act(async () => {
      await result.current.startConversation('Build e-commerce');
    });

    // Finalize
    await act(async () => {
      const response = await result.current.finalizeRequirements();
      expect(response).toEqual(finalizeResponse);
    });

    expect(api.finalizeCEORequirements).toHaveBeenCalledWith('test-123');
    expect(result.current.conversationState).toBe('finalized');
    expect(result.current.messages).toHaveLength(3); // Start + finalize message
    expect(result.current.messages[2].content).toContain('create a plan');
    expect(result.current.isComplete).toBe(true);
    expect(result.current.canSendMessage).toBe(false);
  });

  it('resets the hook state', async () => {
    const startResponse = {
      conversation_id: 'test-123',
      state: 'gathering_requirements',
      message: 'What do you need?',
    };

    api.startCEOChat.mockResolvedValueOnce(startResponse);

    const { result } = renderHook(() => useCEOChat());

    // Start conversation
    await act(async () => {
      await result.current.startConversation('Build something');
    });

    expect(result.current.conversationId).toBe('test-123');
    expect(result.current.messages).toHaveLength(2);

    // Reset
    act(() => {
      result.current.reset();
    });

    expect(result.current.conversationId).toBeNull();
    expect(result.current.messages).toEqual([]);
    expect(result.current.conversationState).toBe('idle');
    expect(result.current.requirements).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('handles loading states correctly', async () => {
    let resolveStart;
    const startPromise = new Promise((resolve) => {
      resolveStart = resolve;
    });

    api.startCEOChat.mockReturnValueOnce(startPromise);

    const { result } = renderHook(() => useCEOChat());

    // Start conversation (will be pending)
    act(() => {
      result.current.startConversation('Test');
    });

    expect(result.current.isLoading).toBe(true);

    // Resolve the promise
    await act(async () => {
      resolveStart({
        conversation_id: 'test-123',
        state: 'gathering_requirements',
        message: 'Started',
      });
      await waitFor(() => expect(result.current.isLoading).toBe(false));
    });

    expect(result.current.isLoading).toBe(false);
  });
});