import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Loader2, MessageSquare, X, Bot, User } from "lucide-react";
import {
  startCEOChat,
  sendCEOChatMessage,
  getCEOChatState,
  finalizeCEORequirements,
  orchestrateWithPrompt,
} from "../lib/api";
import { toast } from "sonner";

export default function CEOChatInterface({
  onClose,
  onRequirementsFinalized,
  initialMessage = "",
}) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [conversationState, setConversationState] = useState("initial");
  const [requirements, setRequirements] = useState(null);
  const [showConfirmButton, setShowConfirmButton] = useState(false);
  const [polishedPrompt, setPolishedPrompt] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Auto-start conversation if initial message is provided
  useEffect(() => {
    if (initialMessage && conversationId === null) {
      handleStartChat(initialMessage);
    }
  }, [initialMessage]);

  const handleStartChat = async (initialMessage) => {
    setIsLoading(true);
    try {
      const response = await startCEOChat(initialMessage);
      setConversationId(response.conversation_id);
      setConversationState(response.state);

      // Add initial user message
      setMessages([
        {
          id: Date.now(),
          type: "user",
          content: initialMessage,
          timestamp: new Date().toISOString(),
        },
        {
          id: Date.now() + 1,
          type: "ceo",
          content: response.message,
          timestamp: new Date().toISOString(),
        },
      ]);

      if (response.requirements) {
        setRequirements(response.requirements);
      }
    } catch (error) {
      console.error("Error starting CEO chat:", error);
      toast.error("Failed to start conversation with CEO");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue("");

    // Add user message immediately
    const newUserMessage = {
      id: Date.now(),
      type: "user",
      content: userMessage,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, newUserMessage]);

    setIsLoading(true);
    try {
      if (!conversationId) {
        // Start conversation with first message
        await handleStartChat(userMessage);
      } else {
        // Continue existing conversation
        const response = await sendCEOChatMessage(conversationId, userMessage);

        // Add CEO response
        const ceoMessage = {
          id: Date.now() + 1,
          type: "ceo",
          content: response.message,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, ceoMessage]);

        setConversationState(response.state);
        if (response.requirements) {
          setRequirements(response.requirements);
        }

        // Check if CEO is asking for confirmation of polished prompt
        if (
          response.state === "awaiting_confirmation" &&
          response.polished_prompt
        ) {
          setPolishedPrompt(response.polished_prompt);
          setShowConfirmButton(true);
        }

        // Also check for requires_confirmation flag
        if (response.requires_confirmation && response.polished_prompt) {
          setPolishedPrompt(response.polished_prompt);
          setShowConfirmButton(true);
        }

        // Check if requirements are complete
        if (response.state === "requirements_complete") {
          setTimeout(() => {
            handleFinalizeRequirements();
          }, 1500);
        }
      }
    } catch (error) {
      console.error("Error sending message:", error);
      toast.error("Failed to send message");
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmPrompt = async () => {
    if (!polishedPrompt) return;

    setIsLoading(true);
    setShowConfirmButton(false);

    try {
      // Add confirmation message
      const confirmMessage = {
        id: Date.now(),
        type: "ceo",
        content:
          "Great! I'm now orchestrating your request with the polished prompt. Creating a plan and delegating tasks to the appropriate agents...",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, confirmMessage]);

      // Call orchestrate endpoint with polished prompt
      const response = await orchestrateWithPrompt(polishedPrompt);

      // Add success message
      const successMessage = {
        id: Date.now() + 1,
        type: "ceo",
        content:
          "Perfect! I've successfully created a plan and delegated tasks to the agents. They will now start working on your request.",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, successMessage]);

      // Call the callback with orchestration result
      setTimeout(() => {
        onRequirementsFinalized({
          requirements: requirements,
          plan: response?.plan || response,
          orchestrationResult: response,
          conversationId: conversationId,
          polishedPrompt: polishedPrompt,
        });
      }, 1000);
    } catch (error) {
      console.error("Error orchestrating with prompt:", error);
      toast.error("Failed to orchestrate the request. Please try again.");
      setShowConfirmButton(true); // Show button again on error
    } finally {
      setIsLoading(false);
    }
  };

  const handleFinalizeRequirements = async () => {
    if (!conversationId) return;

    setIsLoading(true);
    try {
      const response = await finalizeCEORequirements(conversationId);

      // Add final CEO message
      const finalMessage = {
        id: Date.now(),
        type: "ceo",
        content:
          "Great! I have all the information I need. I'll now create a plan and delegate tasks to the appropriate agents.",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, finalMessage]);

      // Add debugging logs
      console.log("[CEO_CHAT_DEBUG] Finalize response:", response);
      console.log(
        "[CEO_CHAT_DEBUG] Response requirements:",
        response.requirements,
      );
      console.log("[CEO_CHAT_DEBUG] Response plan:", response.plan);
      console.log(
        "[CEO_CHAT_DEBUG] Response orchestration_result:",
        response.orchestration_result,
      );

      // Call the callback with finalized requirements and plan
      setTimeout(() => {
        onRequirementsFinalized({
          requirements: response.requirements,
          plan: response.plan,
          orchestrationResult: response.orchestration_result,
          conversationId: conversationId,
        });
      }, 1000);
    } catch (error) {
      console.error("Error finalizing requirements:", error);
      toast.error("Failed to finalize requirements");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          transition={{ type: "spring", damping: 20 }}
          className="relative w-full max-w-2xl h-[600px] rounded-2xl overflow-hidden"
          onClick={(e) => e.stopPropagation()}
          style={{
            background: "rgba(11, 15, 25, 0.95)",
            border: "1px solid rgba(0, 240, 255, 0.3)",
            boxShadow:
              "0 0 60px rgba(0, 240, 255, 0.15), inset 0 0 30px rgba(0, 240, 255, 0.05)",
          }}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-cyan-500/20">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg flex items-center justify-center bg-gradient-to-br from-cyan-500/20 to-fuchsia-500/20">
                <MessageSquare className="h-5 w-5 text-cyan-300" />
              </div>
              <div>
                <h2 className="font-display text-lg text-white">
                  CEO Requirements Gathering
                </h2>
                <p className="text-xs text-slate-400 font-mono">
                  CLAUDE-POWERED ASSISTANT
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="h-8 w-8 rounded-lg flex items-center justify-center hover:bg-white/10 transition-colors"
            >
              <X className="h-4 w-4 text-slate-400" />
            </button>
          </div>

          {/* Messages Container */}
          <div className="h-[calc(100%-140px)] overflow-y-auto px-6 py-4 space-y-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <Bot className="h-12 w-12 text-cyan-300/50 mb-4" />
                <p className="text-slate-400 mb-2">
                  Hi! I'm your CEO assistant.
                </p>
                <p className="text-slate-500 text-sm max-w-md">
                  Tell me about your task, and I'll ask a few clarifying
                  questions to ensure we build exactly what you need.
                </p>
              </div>
            ) : (
              messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex gap-3 ${message.type === "user" ? "justify-end" : "justify-start"}`}
                >
                  {message.type === "ceo" && (
                    <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-cyan-500/20 to-fuchsia-500/20 flex items-center justify-center flex-shrink-0">
                      <Bot className="h-4 w-4 text-cyan-300" />
                    </div>
                  )}
                  <div
                    className={`max-w-[80%] rounded-xl px-4 py-3 ${
                      message.type === "user"
                        ? "bg-cyan-500/20 text-white"
                        : "bg-slate-800/50 text-slate-200"
                    }`}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">
                      {message.content}
                    </p>
                    <p className="text-xs mt-1 opacity-50">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                  {message.type === "user" && (
                    <div className="h-8 w-8 rounded-lg bg-fuchsia-500/20 flex items-center justify-center flex-shrink-0">
                      <User className="h-4 w-4 text-fuchsia-300" />
                    </div>
                  )}
                </motion.div>
              ))
            )}
            {isLoading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex gap-3"
              >
                <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-cyan-500/20 to-fuchsia-500/20 flex items-center justify-center">
                  <Bot className="h-4 w-4 text-cyan-300" />
                </div>
                <div className="bg-slate-800/50 rounded-xl px-4 py-3">
                  <div className="flex gap-1">
                    <span
                      className="h-2 w-2 bg-cyan-300 rounded-full animate-bounce"
                      style={{ animationDelay: "0ms" }}
                    />
                    <span
                      className="h-2 w-2 bg-cyan-300 rounded-full animate-bounce"
                      style={{ animationDelay: "150ms" }}
                    />
                    <span
                      className="h-2 w-2 bg-cyan-300 rounded-full animate-bounce"
                      style={{ animationDelay: "300ms" }}
                    />
                  </div>
                </div>
              </motion.div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="absolute bottom-0 left-0 right-0 px-6 py-4 border-t border-cyan-500/20 bg-[#0B0F19]/80 backdrop-blur-sm">
            {showConfirmButton ? (
              <div className="flex flex-col gap-3">
                <div className="text-sm text-slate-300 bg-slate-800/50 rounded-lg px-4 py-3">
                  <p className="font-medium text-cyan-300 mb-1">
                    Polished Prompt Ready:
                  </p>
                  <p className="text-xs italic">{polishedPrompt}</p>
                </div>
                <button
                  onClick={handleConfirmPrompt}
                  disabled={isLoading}
                  className="w-full py-3 rounded-xl flex items-center justify-center gap-2 transition-all font-medium text-white hover:bg-cyan-500/30 disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{
                    background:
                      "linear-gradient(135deg, rgba(0, 240, 255, 0.2) 0%, rgba(255, 0, 255, 0.2) 100%)",
                    border: "1px solid rgba(0, 240, 255, 0.5)",
                  }}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Orchestrating...
                    </>
                  ) : (
                    <>Confirm and Start Orchestration</>
                  )}
                </button>
              </div>
            ) : (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage();
                }}
                className="flex gap-3"
              >
                <input
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Type your response..."
                  disabled={
                    isLoading || conversationState === "requirements_complete"
                  }
                  className="flex-1 bg-slate-800/50 rounded-xl px-4 py-3 text-sm text-white placeholder:text-slate-500 outline-none focus:ring-2 focus:ring-cyan-500/50 disabled:opacity-50 disabled:cursor-not-allowed"
                />
                <button
                  type="submit"
                  disabled={
                    isLoading ||
                    !inputValue.trim() ||
                    conversationState === "requirements_complete"
                  }
                  className="h-11 w-11 rounded-xl flex items-center justify-center transition-all disabled:opacity-40 disabled:cursor-not-allowed hover:bg-cyan-400/20"
                  style={{
                    background: "rgba(0, 240, 255, 0.15)",
                    border: "1px solid rgba(0, 240, 255, 0.4)",
                  }}
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 text-cyan-300 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4 text-cyan-300" />
                  )}
                </button>
              </form>
            )}
          </div>

          {/* Requirements Summary (if available) */}
          {requirements && conversationState === "requirements_complete" && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="absolute top-16 right-6 w-64 p-4 rounded-lg bg-slate-800/90 border border-cyan-500/30"
            >
              <h3 className="font-mono text-xs uppercase tracking-wider text-cyan-300 mb-2">
                Requirements Summary
              </h3>
              <div className="space-y-2 text-xs text-slate-300">
                {requirements.purpose && (
                  <div>
                    <span className="text-cyan-400">Purpose:</span>{" "}
                    {requirements.purpose}
                  </div>
                )}
                {requirements.target_audience && (
                  <div>
                    <span className="text-cyan-400">Audience:</span>{" "}
                    {requirements.target_audience}
                  </div>
                )}
                {requirements.key_features && (
                  <div>
                    <span className="text-cyan-400">Features:</span>{" "}
                    {requirements.key_features.join(", ")}
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
