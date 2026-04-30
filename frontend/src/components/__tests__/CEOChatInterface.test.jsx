import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import CEOChatInterface from '../CEOChatInterface';
import * as api from '../../lib/api';

// Mock the API module
vi.mock('../../lib/api');

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }) => children,
}));

// Mock sonner
vi.mock('sonner', () => ({
  toast: {
    error: vi.fn(),
  },
}));

describe('CEOChatInterface', () => {
  const mockOnClose = vi.fn();
  const mockOnRequirementsFinalized = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the chat interface with initial state', () => {
    render(
      <CEOChatInterface
        onClose={mockOnClose}
        onRequirementsFinalized={mockOnRequirementsFinalized}
      />
    );

    expect(screen.getByText('CEO Requirements Gathering')).toBeInTheDocument();
    expect(screen.getByText('CLAUDE-POWERED ASSISTANT')).toBeInTheDocument();
    expect(screen.getByText("Hi! I'm your CEO assistant.")).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Type your response...')).toBeInTheDocument();
  });

  it('closes the chat interface when close button is clicked', () => {
    render(
      <CEOChatInterface
        onClose={mockOnClose}
        onRequirementsFinalized={mockOnRequirementsFinalized}
      />
    );

    const closeButton = screen.getByRole('button', { name: '' });
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('starts a conversation when initial message is provided', async () => {
    const mockResponse = {
      conversation_id: 'test-conv-123',
      state: 'gathering_requirements',
      message: 'Thanks for your request! Let me ask you a few questions...',
    };

    api.startCEOChat.mockResolvedValueOnce(mockResponse);

    render(
      <CEOChatInterface
        onClose={mockOnClose}
        onRequirementsFinalized={mockOnRequirementsFinalized}
        initialMessage="I want to build a new feature"
      />
    );

    await waitFor(() => {
      expect(api.startCEOChat).toHaveBeenCalledWith('I want to build a new feature');
      expect(screen.getByText('I want to build a new feature')).toBeInTheDocument();
      expect(screen.getByText(mockResponse.message)).toBeInTheDocument();
    });
  });

  it('sends a message when user types and submits', async () => {
    const mockStartResponse = {
      conversation_id: 'test-conv-123',
      state: 'gathering_requirements',
      message: 'What is your target audience?',
    };

    const mockSendResponse = {
      state: 'gathering_requirements',
      message: 'Great! What are the key features you want?',
    };

    api.startCEOChat.mockResolvedValueOnce(mockStartResponse);
    api.sendCEOChatMessage.mockResolvedValueOnce(mockSendResponse);

    render(
      <CEOChatInterface
        onClose={mockOnClose}
        onRequirementsFinalized={mockOnRequirementsFinalized}
      />
    );

    const input = screen.getByPlaceholderText('Type your response...');
    const sendButton = screen.getByRole('button', { name: '' });

    // Type and send first message
    fireEvent.change(input, { target: { value: 'I need a dashboard' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(api.startCEOChat).toHaveBeenCalledWith('I need a dashboard');
      expect(screen.getByText('I need a dashboard')).toBeInTheDocument();
      expect(screen.getByText(mockStartResponse.message)).toBeInTheDocument();
    });

    // Type and send second message
    fireEvent.change(input, { target: { value: 'For developers' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(api.sendCEOChatMessage).toHaveBeenCalledWith('test-conv-123', 'For developers');
      expect(screen.getByText('For developers')).toBeInTheDocument();
      expect(screen.getByText(mockSendResponse.message)).toBeInTheDocument();
    });
  });

  it('finalizes requirements when conversation is complete', async () => {
    const mockStartResponse = {
      conversation_id: 'test-conv-123',
      state: 'gathering_requirements',
      message: 'What do you want to build?',
    };

    const mockCompleteResponse = {
      state: 'requirements_complete',
      message: 'I have all the information I need!',
      requirements: {
        purpose: 'Dashboard',
        target_audience: 'Developers',
        key_features: ['Analytics', 'Monitoring'],
      },
    };

    const mockFinalizeResponse = {
      requirements: mockCompleteResponse.requirements,
      plan: {
        mode: 'multi_agent',
        steps: [{ agent_id: 'frontend_engineer', instruction: 'Build dashboard' }],
      },
    };

    api.startCEOChat.mockResolvedValueOnce(mockStartResponse);
    api.sendCEOChatMessage.mockResolvedValueOnce(mockCompleteResponse);
    api.finalizeCEORequirements.mockResolvedValueOnce(mockFinalizeResponse);

    render(
      <CEOChatInterface
        onClose={mockOnClose}
        onRequirementsFinalized={mockOnRequirementsFinalized}
      />
    );

    const input = screen.getByPlaceholderText('Type your response...');
    const sendButton = screen.getByRole('button', { name: '' });

    // Start conversation
    fireEvent.change(input, { target: { value: 'Build a dashboard' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText('Build a dashboard')).toBeInTheDocument();
    });

    // Complete requirements
    fireEvent.change(input, { target: { value: 'For developers with analytics' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(api.finalizeCEORequirements).toHaveBeenCalledWith('test-conv-123');
      expect(mockOnRequirementsFinalized).toHaveBeenCalledWith({
        requirements: mockFinalizeResponse.requirements,
        plan: mockFinalizeResponse.plan,
        conversationId: 'test-conv-123',
      });
    });
  });

  it('displays loading state while processing', async () => {
    const mockResponse = new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          conversation_id: 'test-conv-123',
          state: 'gathering_requirements',
          message: 'Processing...',
        });
      }, 100);
    });

    api.startCEOChat.mockReturnValueOnce(mockResponse);

    render(
      <CEOChatInterface
        onClose={mockOnClose}
        onRequirementsFinalized={mockOnRequirementsFinalized}
      />
    );

    const input = screen.getByPlaceholderText('Type your response...');
    const sendButton = screen.getByRole('button', { name: '' });

    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);

    // Check for loading indicator
    await waitFor(() => {
      const loadingDots = screen.getAllByRole('generic').filter(
        el => el.className.includes('animate-bounce')
      );
      expect(loadingDots).toHaveLength(3);
    });
  });

  it('displays requirements summary when available', async () => {
    const mockResponse = {
      conversation_id: 'test-conv-123',
      state: 'requirements_complete',
      message: 'Requirements gathered!',
      requirements: {
        purpose: 'E-commerce platform',
        target_audience: 'Small businesses',
        key_features: ['Product catalog', 'Shopping cart', 'Payment'],
      },
    };

    api.startCEOChat.mockResolvedValueOnce(mockResponse);

    render(
      <CEOChatInterface
        onClose={mockOnClose}
        onRequirementsFinalized={mockOnRequirementsFinalized}
        initialMessage="Build an e-commerce site"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Requirements Summary')).toBeInTheDocument();
      expect(screen.getByText('E-commerce platform')).toBeInTheDocument();
      expect(screen.getByText('Small businesses')).toBeInTheDocument();
      expect(screen.getByText('Product catalog, Shopping cart, Payment')).toBeInTheDocument();
    });
  });
});