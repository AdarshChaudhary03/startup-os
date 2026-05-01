import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import CEOChatInterface from "../CEOChatInterface";
import * as api from "../../lib/api";
import { toast } from "sonner";

// Mock the API module
jest.mock("../../lib/api");
jest.mock("sonner");

// Mock scrollIntoView since it's not available in jsdom
window.HTMLElement.prototype.scrollIntoView = jest.fn();

describe("CEOChatInterface - Confirm Button Functionality", () => {
  const mockOnClose = jest.fn();
  const mockOnRequirementsFinalized = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Confirm Button Visibility", () => {
    it("should not show confirm button initially", () => {
      render(
        <CEOChatInterface
          onClose={mockOnClose}
          onRequirementsFinalized={mockOnRequirementsFinalized}
        />,
      );

      expect(
        screen.queryByText("Confirm and Start Orchestration"),
      ).not.toBeInTheDocument();
    });

    it("should show confirm button when CEO sends awaiting_confirmation state with polished prompt", async () => {
      const mockConversationId = "test-conv-123";
      const mockPolishedPrompt =
        "Create a web application with user authentication and dashboard";

      // Mock API responses
      api.startCEOChat.mockResolvedValue({
        conversation_id: mockConversationId,
        state: "gathering_requirements",
        message: "Tell me about your project",
      });

      api.sendCEOChatMessage.mockResolvedValue({
        state: "awaiting_confirmation",
        message: "Here is your polished prompt. Please confirm to proceed.",
        polished_prompt: mockPolishedPrompt,
      });

      render(
        <CEOChatInterface
          onClose={mockOnClose}
          onRequirementsFinalized={mockOnRequirementsFinalized}
          initialMessage="I need a web app"
        />,
      );

      // Wait for initial message
      await waitFor(() => {
        expect(api.startCEOChat).toHaveBeenCalled();
      });

      // Send a message to trigger awaiting_confirmation state
      const input = screen.getByPlaceholderText("Type your response...");
      fireEvent.change(input, { target: { value: "Yes, with login feature" } });
      fireEvent.submit(input.closest("form"));

      // Wait for confirm button to appear
      await waitFor(() => {
        expect(
          screen.getByText("Confirm and Start Orchestration"),
        ).toBeInTheDocument();
      });

      // Verify polished prompt is displayed
      expect(screen.getByText(mockPolishedPrompt)).toBeInTheDocument();
    });
  });

  describe("Orchestration Integration", () => {
    it("should call orchestrateWithPrompt when confirm button is clicked", async () => {
      const mockConversationId = "test-conv-123";
      const mockPolishedPrompt =
        "Create a web application with user authentication";
      const mockOrchestrationResponse = {
        plan: {
          agents: ["frontend", "backend"],
          tasks: ["Create UI", "Setup auth"],
        },
      };

      // Setup mocks
      api.startCEOChat.mockResolvedValue({
        conversation_id: mockConversationId,
        state: "gathering_requirements",
        message: "Tell me about your project",
      });

      api.sendCEOChatMessage.mockResolvedValue({
        state: "awaiting_confirmation",
        message: "Please confirm the polished prompt",
        polished_prompt: mockPolishedPrompt,
      });

      api.orchestrateWithPrompt.mockResolvedValue(mockOrchestrationResponse);

      render(
        <CEOChatInterface
          onClose={mockOnClose}
          onRequirementsFinalized={mockOnRequirementsFinalized}
          initialMessage="Build a web app"
        />,
      );

      // Get to confirmation state
      await waitFor(() => expect(api.startCEOChat).toHaveBeenCalled());

      const input = screen.getByPlaceholderText("Type your response...");
      fireEvent.change(input, { target: { value: "With authentication" } });
      fireEvent.submit(input.closest("form"));

      await waitFor(() => {
        expect(
          screen.getByText("Confirm and Start Orchestration"),
        ).toBeInTheDocument();
      });

      // Click confirm button
      const confirmButton = screen.getByText("Confirm and Start Orchestration");
      fireEvent.click(confirmButton);

      // Verify orchestration was called with correct prompt
      await waitFor(() => {
        expect(api.orchestrateWithPrompt).toHaveBeenCalledWith(
          mockPolishedPrompt,
        );
      });

      // Verify callback was called with results
      await waitFor(() => {
        expect(mockOnRequirementsFinalized).toHaveBeenCalledWith(
          expect.objectContaining({
            plan: mockOrchestrationResponse.plan,
            orchestrationResult: mockOrchestrationResponse,
            polishedPrompt: mockPolishedPrompt,
          }),
        );
      });
    });

    it("should show loading state while orchestrating", async () => {
      const mockPolishedPrompt = "Create app";

      // Setup delayed orchestration response
      api.orchestrateWithPrompt.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100)),
      );

      api.startCEOChat.mockResolvedValue({
        conversation_id: "test-123",
        state: "gathering_requirements",
        message: "Tell me more",
      });

      api.sendCEOChatMessage.mockResolvedValue({
        state: "awaiting_confirmation",
        message: "Confirm?",
        polished_prompt: mockPolishedPrompt,
      });

      render(
        <CEOChatInterface
          onClose={mockOnClose}
          onRequirementsFinalized={mockOnRequirementsFinalized}
          initialMessage="Build app"
        />,
      );

      // Get to confirmation state
      await waitFor(() => expect(api.startCEOChat).toHaveBeenCalled());

      const input = screen.getByPlaceholderText("Type your response...");
      fireEvent.change(input, { target: { value: "Yes" } });
      fireEvent.submit(input.closest("form"));

      await waitFor(() => {
        expect(
          screen.getByText("Confirm and Start Orchestration"),
        ).toBeInTheDocument();
      });

      // Click confirm
      fireEvent.click(screen.getByText("Confirm and Start Orchestration"));

      // Should show loading state
      await waitFor(() => {
        expect(screen.getByText("Orchestrating...")).toBeInTheDocument();
      });
      expect(screen.getByRole("button")).toBeDisabled();
    });
  });

  describe("Error Handling", () => {
    it("should handle orchestration errors gracefully", async () => {
      const mockPolishedPrompt = "Create app";
      const mockError = new Error("Orchestration failed");

      // Setup mocks
      api.orchestrateWithPrompt.mockRejectedValue(mockError);
      api.startCEOChat.mockResolvedValue({
        conversation_id: "test-123",
        state: "gathering_requirements",
        message: "Tell me more",
      });

      api.sendCEOChatMessage.mockResolvedValue({
        state: "awaiting_confirmation",
        message: "Confirm?",
        polished_prompt: mockPolishedPrompt,
      });

      render(
        <CEOChatInterface
          onClose={mockOnClose}
          onRequirementsFinalized={mockOnRequirementsFinalized}
          initialMessage="Build app"
        />,
      );

      // Get to confirmation state
      await waitFor(() => expect(api.startCEOChat).toHaveBeenCalled());

      const input = screen.getByPlaceholderText("Type your response...");
      fireEvent.change(input, { target: { value: "Yes" } });
      fireEvent.submit(input.closest("form"));

      await waitFor(() => {
        expect(
          screen.getByText("Confirm and Start Orchestration"),
        ).toBeInTheDocument();
      });

      // Click confirm
      fireEvent.click(screen.getByText("Confirm and Start Orchestration"));

      // Wait for error handling
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(
          "Failed to orchestrate the request. Please try again.",
        );
      });

      // Confirm button should be visible again after error
      await waitFor(() => {
        expect(
          screen.getByText("Confirm and Start Orchestration"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("Message Flow", () => {
    it("should display appropriate messages during orchestration flow", async () => {
      const mockPolishedPrompt = "Create a web app";

      api.startCEOChat.mockResolvedValue({
        conversation_id: "test-123",
        state: "gathering_requirements",
        message: "Tell me about your project",
      });

      api.sendCEOChatMessage.mockResolvedValue({
        state: "awaiting_confirmation",
        message: "Here is your polished prompt",
        polished_prompt: mockPolishedPrompt,
      });

      api.orchestrateWithPrompt.mockResolvedValue({
        plan: { agents: ["frontend"] },
      });

      render(
        <CEOChatInterface
          onClose={mockOnClose}
          onRequirementsFinalized={mockOnRequirementsFinalized}
          initialMessage="I need a web app"
        />,
      );

      // Wait for initial setup
      await waitFor(() => expect(api.startCEOChat).toHaveBeenCalled());

      // Send message to trigger confirmation
      const input = screen.getByPlaceholderText("Type your response...");
      fireEvent.change(input, { target: { value: "With user auth" } });
      fireEvent.submit(input.closest("form"));

      await waitFor(() => {
        expect(
          screen.getByText("Confirm and Start Orchestration"),
        ).toBeInTheDocument();
      });

      // Click confirm
      fireEvent.click(screen.getByText("Confirm and Start Orchestration"));

      // Check for orchestration messages
      await waitFor(() => {
        expect(
          screen.getByText(/I'm now orchestrating your request/),
        ).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(
          screen.getByText(/successfully created a plan/),
        ).toBeInTheDocument();
      });
    });
  });
});
