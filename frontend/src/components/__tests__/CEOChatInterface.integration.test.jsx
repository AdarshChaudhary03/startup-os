import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { CEOChatInterface } from "../CEOChatInterface";
import * as api from "../../lib/api";

// Mock the API module
jest.mock("../../lib/api");

// Mock sonner (toast library used in the project)
jest.mock("sonner", () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
  },
}));

describe("CEOChatInterface Integration Tests", () => {
  const mockOnClose = jest.fn();
  const mockOnRequirementsFinalized = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("API Integration", () => {
    it("should handle successful chat start with proper API response", async () => {
      const mockResponse = {
        conversation_id: "test-conv-123",
        state: "gathering_requirements",
        message: "Hello! Let me help you understand your requirements better.",
        requirements: {},
        timestamp: new Date().toISOString(),
      };

      api.startCEOChat.mockResolvedValueOnce(mockResponse);

      render(
        <CEOChatInterface
          isOpen={true}
          onClose={mockOnClose}
          onRequirementsFinalized={mockOnRequirementsFinalized}
          initialMessage="Build a user authentication system"
        />,
      );

      // Wait for the initial message to be processed
      await waitFor(() => {
        expect(api.startCEOChat).toHaveBeenCalledWith(
          "Build a user authentication system",
        );
      });

      // Check that the CEO's response is displayed
      await waitFor(() => {
        expect(screen.getByText(mockResponse.message)).toBeInTheDocument();
      });
    });

    it("should handle 422 error gracefully without body stream issues", async () => {
      // Simulate a 422 error response
      const errorResponse = new Error("initial_message is required");
      api.startCEOChat.mockRejectedValueOnce(errorResponse);

      render(
        <CEOChatInterface
          isOpen={true}
          onClose={mockOnClose}
          onRequirementsFinalized={mockOnRequirementsFinalized}
          initialMessage=""
        />,
      );

      // The component should handle the error without crashing
      await waitFor(() => {
        expect(
          screen.getByText(/Hi! I'm your CEO assistant/i),
        ).toBeInTheDocument();
      });
    });

    it("should send messages correctly and handle responses", async () => {
      const mockStartResponse = {
        conversation_id: "test-conv-123",
        state: "gathering_requirements",
        message: "What is the main purpose of your project?",
        requirements: {},
      };

      const mockMessageResponse = {
        conversation_id: "test-conv-123",
        state: "gathering_requirements",
        message: "Great! Who is your target audience?",
        requirements: { purpose: "user authentication" },
      };

      api.startCEOChat.mockResolvedValueOnce(mockStartResponse);
      api.sendCEOChatMessage.mockResolvedValueOnce(mockMessageResponse);

      const { getByPlaceholderText, getByRole } = render(
        <CEOChatInterface
          isOpen={true}
          onClose={mockOnClose}
          onRequirementsFinalized={mockOnRequirementsFinalized}
          initialMessage="Build an auth system"
        />,
      );

      // Wait for initial chat to start
      await waitFor(() => {
        expect(screen.getByText(mockStartResponse.message)).toBeInTheDocument();
      });

      // Type and send a message
      const input = getByPlaceholderText("Type your response...");
      const sendButton = getByRole("button", { name: /send/i });

      fireEvent.change(input, { target: { value: "For enterprise users" } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(api.sendCEOChatMessage).toHaveBeenCalledWith(
          "test-conv-123",
          "For enterprise users",
        );
      });

      // Check that the response is displayed
      await waitFor(() => {
        expect(
          screen.getByText(mockMessageResponse.message),
        ).toBeInTheDocument();
      });
    });

    it("should finalize requirements when conversation is complete", async () => {
      const mockStartResponse = {
        conversation_id: "test-conv-123",
        state: "gathering_requirements",
        message: "Initial message",
        requirements: {},
      };

      const mockCompleteResponse = {
        conversation_id: "test-conv-123",
        state: "requirements_complete",
        message: "I have all the information I need.",
        requirements: {
          purpose: "authentication",
          target_audience: "enterprise",
          key_features: ["SSO", "MFA"],
        },
      };

      const mockFinalizeResponse = {
        requirements: mockCompleteResponse.requirements,
        plan: {
          agents: ["backend_agent", "security_agent"],
          steps: ["Design API", "Implement auth"],
        },
      };

      api.startCEOChat.mockResolvedValueOnce(mockStartResponse);
      api.sendCEOChatMessage.mockResolvedValueOnce(mockCompleteResponse);
      api.finalizeCEORequirements.mockResolvedValueOnce(mockFinalizeResponse);

      render(
        <CEOChatInterface
          isOpen={true}
          onClose={mockOnClose}
          onRequirementsFinalized={mockOnRequirementsFinalized}
          initialMessage="Build auth"
        />,
      );

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText(mockStartResponse.message)).toBeInTheDocument();
      });

      // Send a message that completes requirements
      const input = screen.getByPlaceholderText("Type your response...");
      const sendButton = screen.getByRole("button", { name: /send/i });

      fireEvent.change(input, {
        target: { value: "Enterprise users with SSO" },
      });
      fireEvent.click(sendButton);

      // Wait for finalization
      await waitFor(() => {
        expect(api.finalizeCEORequirements).toHaveBeenCalledWith(
          "test-conv-123",
        );
      });

      await waitFor(() => {
        expect(mockOnRequirementsFinalized).toHaveBeenCalledWith({
          requirements: mockFinalizeResponse.requirements,
          plan: mockFinalizeResponse.plan,
          conversationId: "test-conv-123",
        });
      });
    });

    it("should handle API errors without consuming response body multiple times", async () => {
      // Create a mock Response object that simulates the body stream issue
      const mockResponse = {
        ok: false,
        status: 422,
        statusText: "Unprocessable Entity",
        json: jest.fn().mockResolvedValue({ detail: "Validation error" }),
        text: jest
          .fn()
          .mockRejectedValue(new Error("body stream already read")),
      };

      // Mock fetch to return our mock response
      global.fetch = jest.fn().mockResolvedValue(mockResponse);

      render(
        <CEOChatInterface
          isOpen={true}
          onClose={mockOnClose}
          onRequirementsFinalized={mockOnRequirementsFinalized}
          initialMessage="Test message"
        />,
      );

      // The component should handle the error gracefully
      await waitFor(() => {
        // Component should still be rendered
        expect(
          screen.getByText(/Hi! I'm your CEO assistant/i),
        ).toBeInTheDocument();
      });

      // Restore fetch
      global.fetch.mockRestore();
    });
  });

  describe("Error Recovery", () => {
    it("should recover from network errors and allow retry", async () => {
      // First call fails
      api.startCEOChat.mockRejectedValueOnce(new Error("Network error"));

      // Second call succeeds
      const mockResponse = {
        conversation_id: "test-conv-123",
        state: "gathering_requirements",
        message: "Hello! How can I help?",
        requirements: {},
      };
      api.startCEOChat.mockResolvedValueOnce(mockResponse);

      render(
        <CEOChatInterface
          isOpen={true}
          onClose={mockOnClose}
          onRequirementsFinalized={mockOnRequirementsFinalized}
          initialMessage="Build something"
        />,
      );

      // Wait for error
      await waitFor(() => {
        expect(api.startCEOChat).toHaveBeenCalledTimes(1);
      });

      // User can still type and send a message to retry
      const input = screen.getByPlaceholderText("Type your response...");
      const sendButton = screen.getByRole("button", { name: /send/i });

      fireEvent.change(input, { target: { value: "Build an app" } });
      fireEvent.click(sendButton);

      // Should retry with new message
      await waitFor(() => {
        expect(api.startCEOChat).toHaveBeenCalledTimes(2);
        expect(api.startCEOChat).toHaveBeenLastCalledWith("Build an app");
      });

      // Should show success response
      await waitFor(() => {
        expect(screen.getByText(mockResponse.message)).toBeInTheDocument();
      });
    });
  });
});
