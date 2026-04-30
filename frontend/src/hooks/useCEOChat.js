import { useState, useCallback } from 'react';
import { startCEOChat, sendCEOChatMessage, getCEOChatState, finalizeCEORequirements } from '../lib/api';

export function useCEOChat() {
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [conversationState, setConversationState] = useState('idle');
  const [requirements, setRequirements] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const startConversation = useCallback(async (initialMessage) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await startCEOChat(initialMessage);
      
      setConversationId(response.conversation_id);
      setConversationState(response.state);
      
      // Initialize messages with user message and CEO response
      setMessages([
        {
          id: `user-${Date.now()}`,
          type: 'user',
          content: initialMessage,
          timestamp: new Date().toISOString(),
        },
        {
          id: `ceo-${Date.now() + 1}`,
          type: 'ceo',
          content: response.message,
          timestamp: new Date().toISOString(),
        },
      ]);
      
      if (response.requirements) {
        setRequirements(response.requirements);
      }
      
      return response;
    } catch (err) {
      setError(err.message || 'Failed to start conversation');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const sendMessage = useCallback(async (message) => {
    if (!conversationId) {
      throw new Error('No active conversation');
    }
    
    setIsLoading(true);
    setError(null);
    
    // Add user message immediately
    const userMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);
    
    try {
      const response = await sendCEOChatMessage(conversationId, message);
      
      // Add CEO response
      const ceoMessage = {
        id: `ceo-${Date.now() + 1}`,
        type: 'ceo',
        content: response.message,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, ceoMessage]);
      
      setConversationState(response.state);
      
      if (response.requirements) {
        setRequirements(response.requirements);
      }
      
      return response;
    } catch (err) {
      setError(err.message || 'Failed to send message');
      // Remove the user message on error
      setMessages(prev => prev.filter(m => m.id !== userMessage.id));
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [conversationId]);

  const getState = useCallback(async () => {
    if (!conversationId) {
      throw new Error('No active conversation');
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await getCEOChatState(conversationId);
      setConversationState(response.state);
      
      if (response.requirements) {
        setRequirements(response.requirements);
      }
      
      return response;
    } catch (err) {
      setError(err.message || 'Failed to get conversation state');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [conversationId]);

  const finalizeRequirements = useCallback(async () => {
    if (!conversationId) {
      throw new Error('No active conversation');
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await finalizeCEORequirements(conversationId);
      
      // Add final message
      const finalMessage = {
        id: `ceo-${Date.now()}`,
        type: 'ceo',
        content: 'Great! I have all the information I need. I\'ll now create a plan and delegate tasks to the appropriate agents.',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, finalMessage]);
      
      setConversationState('finalized');
      
      return response;
    } catch (err) {
      setError(err.message || 'Failed to finalize requirements');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [conversationId]);

  const reset = useCallback(() => {
    setConversationId(null);
    setMessages([]);
    setConversationState('idle');
    setRequirements(null);
    setError(null);
    setIsLoading(false);
  }, []);

  return {
    // State
    conversationId,
    messages,
    conversationState,
    requirements,
    isLoading,
    error,
    
    // Actions
    startConversation,
    sendMessage,
    getState,
    finalizeRequirements,
    reset,
    
    // Computed
    isActive: conversationId !== null,
    canSendMessage: conversationId && !isLoading && conversationState !== 'requirements_complete' && conversationState !== 'finalized',
    isComplete: conversationState === 'requirements_complete' || conversationState === 'finalized',
  };
}