import { motion } from "framer-motion";
import { Crown, Mic, MicOff, Volume2 } from "lucide-react";
import { useState, useEffect, useRef, useCallback } from "react";

const STATUS_LABEL = {
  idle: "STANDING BY",
  listening: "LISTENING...",
  processing: "PROCESSING...",
  speaking: "SPEAKING...",
  thinking: "THINKING…",
  routing: "ROUTING TASK",
  done: "TASK COMPLETE",
};

const STATUS_COLOR = {
  idle: "#3A4B6E",
  listening: "#00FF88",
  processing: "#FF00FF",
  speaking: "#00F0FF",
  thinking: "#00F0FF",
  routing: "#FF00FF",
  done: "#00FF88",
};

// ElevenLabs API configuration
const ELEVENLABS_API_KEY =
  process.env.REACT_APP_ELEVENLABS_API_KEY ||
  "sk_46362f2b7ddefb5c9c096f4daf820afa526a6ca59b5db90a";
const ELEVENLABS_VOICE_ID =
  process.env.REACT_APP_ELEVENLABS_VOICE_ID || "CwhRBWXzGAHq8TQ4Fs17";
const ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech";

export default function CEONodev2({
  status = "idle",
  onTaskReceived,
  apiKey = ELEVENLABS_API_KEY,
  voiceId = ELEVENLABS_VOICE_ID,
}) {
  const [isListening, setIsListening] = useState(false);
  const [currentStatus, setCurrentStatus] = useState(status);
  const [transcript, setTranscript] = useState("");
  const [isWakeWordDetected, setIsWakeWordDetected] = useState(false);
  const [conversationState, setConversationState] = useState("idle"); // idle, listening_for_task, waiting_for_confirmation, executing
  const [pendingTask, setPendingTask] = useState("");
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false);

  const recognitionRef = useRef(null);
  const audioContextRef = useRef(null);
  const audioRef = useRef(null);

  const color = STATUS_COLOR[currentStatus];
  const isActive = currentStatus !== "idle";

  // Initialize speech recognition
  useEffect(() => {
    if (
      !("webkitSpeechRecognition" in window) &&
      !("SpeechRecognition" in window)
    ) {
      console.warn("Speech recognition not supported in this browser");
      return;
    }

    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    recognitionRef.current = new SpeechRecognition();

    recognitionRef.current.continuous = true;
    recognitionRef.current.interimResults = true;
    recognitionRef.current.lang = "en-US";

    recognitionRef.current.onstart = () => {
      console.log("🎤 ALEX DEBUG: Speech recognition started");
      setIsListening(true);
    };

    recognitionRef.current.onresult = (event) => {
      let finalTranscript = "";
      let interimTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      const fullTranscript = (
        finalTranscript + interimTranscript
      ).toLowerCase();
      setTranscript(fullTranscript);

      // Check for wake word "Alex"
      if (!isWakeWordDetected && fullTranscript.includes("alex")) {
        setIsWakeWordDetected(true);
        setCurrentStatus("listening");
        setConversationState("listening_for_task");
        console.log('🔔 ALEX DEBUG: Wake word "Alex" detected!');
        console.log("🗣️ ALEX DEBUG: About to call speakText with greeting");

        // Play a confirmation sound or speak
        speakText("Yes, I'm listening. How can I help you?");
      }

      // If wake word detected and we have a complete sentence
      if (isWakeWordDetected && finalTranscript.trim()) {
        // Only process if it's not just the wake word
        const cleanCommand = finalTranscript.replace(/alex/gi, "").trim();
        if (cleanCommand.length > 0) {
          handleUserCommand(finalTranscript.trim());
        }
      }
    };

    recognitionRef.current.onerror = (event) => {
      console.error("❌ ALEX DEBUG: Speech recognition error:", event.error);
      setIsListening(false);
      setCurrentStatus("idle");
    };

    recognitionRef.current.onend = () => {
      console.log("🔇 ALEX DEBUG: Speech recognition ended");
      setIsListening(false);

      // Restart listening if we're still in active mode
      if (isWakeWordDetected) {
        console.log("🔄 ALEX DEBUG: Restarting speech recognition in 1 second");
        setTimeout(() => {
          startListening();
        }, 1000);
      } else {
        console.log("😴 ALEX DEBUG: Setting status to idle");
        setCurrentStatus("idle");
      }
    };

    // Start listening immediately
    startListening();

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [isWakeWordDetected]);

  const startListening = useCallback(() => {
    if (recognitionRef.current && !isListening) {
      try {
        recognitionRef.current.start();
        if (!isWakeWordDetected) {
          setCurrentStatus("idle"); // Waiting for wake word
        }
      } catch (error) {
        console.error("Error starting speech recognition:", error);
      }
    }
  }, [isListening, isWakeWordDetected]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
      setIsWakeWordDetected(false);
      setCurrentStatus("idle");
      setConversationState("idle");
      setAwaitingConfirmation(false);
      setPendingTask("");
      // Say goodbye when manually stopped
      speakText("Goodbye! Say Alex to wake me up again.");
    }
  }, []);

  const handleUserCommand = useCallback(
    async (command) => {
      console.log("📝 ALEX DEBUG: Processing command:", command);
      console.log(
        "🔄 ALEX DEBUG: Current conversation state:",
        conversationState,
      );
      console.log(
        "⏳ ALEX DEBUG: Awaiting confirmation:",
        awaitingConfirmation,
      );
      setCurrentStatus("processing");

      try {
        // Remove wake word from command
        const cleanCommand = command.replace(/alex/gi, "").trim();

        if (cleanCommand) {
          // Check if user is responding to a confirmation request
          if (awaitingConfirmation) {
            const response = cleanCommand.toLowerCase();
            if (
              response.includes("yes") ||
              response.includes("confirm") ||
              response.includes("proceed") ||
              response.includes("do it")
            ) {
              // User confirmed, execute the task
              await speakText("Understood. I will execute this task now.");
              setAwaitingConfirmation(false);
              setConversationState("executing");

              if (onTaskReceived) {
                setCurrentStatus("routing");
                await onTaskReceived(pendingTask);
                setCurrentStatus("done");
                await speakText(
                  "Task has been completed successfully. Is there anything else I can help you with?",
                );
              }
              setPendingTask("");
              setConversationState("listening_for_task");
            } else if (
              response.includes("no") ||
              response.includes("cancel") ||
              response.includes("stop")
            ) {
              // User cancelled
              await speakText(
                "Understood. Task cancelled. What else can I help you with?",
              );
              setAwaitingConfirmation(false);
              setPendingTask("");
              setConversationState("listening_for_task");
            } else {
              // Unclear response, ask again
              await speakText(
                "I didn't understand. Please say yes to confirm or no to cancel the task.",
              );
            }
          } else {
            // This is a new task request
            setPendingTask(cleanCommand);
            setConversationState("waiting_for_confirmation");
            setAwaitingConfirmation(true);

            // Ask for confirmation before executing
            await speakText(
              `I understand you want me to: ${cleanCommand}. Should I proceed with this task? Please say yes to confirm or no to cancel.`,
            );
          }
        } else {
          // Empty command, just greet or ask what they need
          await speakText(
            "Hello! I'm Alex, your AI assistant. How can I help you today?",
          );
          setConversationState("listening_for_task");
        }
      } catch (error) {
        console.error("Error processing command:", error);
        await speakText(
          "I encountered an error processing your request. Please try again.",
        );
        setAwaitingConfirmation(false);
        setPendingTask("");
        setConversationState("listening_for_task");
      }

      // Keep listening for more input
      setCurrentStatus("listening");
    },
    [onTaskReceived, awaitingConfirmation, pendingTask],
  );

  const speakText = useCallback(
    async (text) => {
      console.log("🎤 ALEX DEBUG: speakText called with:", text);
      console.log("🔑 ALEX DEBUG: API Key exists:", !!apiKey);
      console.log("🎵 ALEX DEBUG: Voice ID exists:", !!voiceId);

      if (!apiKey || !voiceId) {
        console.warn(
          "❌ ALEX DEBUG: ElevenLabs API key or Voice ID not configured",
        );
        console.log("📝 ALEX DEBUG: Falling back to browser speech synthesis");

        // Fallback to browser's built-in speech synthesis
        if ("speechSynthesis" in window) {
          setCurrentStatus("speaking");
          const utterance = new SpeechSynthesisUtterance(text);
          utterance.rate = 0.9;
          utterance.pitch = 1;
          utterance.volume = 1;

          utterance.onstart = () => {
            console.log("🗣️ ALEX DEBUG: Browser speech started");
          };

          utterance.onend = () => {
            console.log("✅ ALEX DEBUG: Browser speech ended");
            setCurrentStatus("listening");
          };

          utterance.onerror = (error) => {
            console.error("❌ ALEX DEBUG: Browser speech error:", error);
            setCurrentStatus("listening");
          };

          window.speechSynthesis.speak(utterance);
        } else {
          console.error("❌ ALEX DEBUG: No speech synthesis available");
        }
        return;
      }

      setCurrentStatus("speaking");
      console.log("🚀 ALEX DEBUG: Starting ElevenLabs TTS request");

      try {
        // Updated request body to match your curl command format
        const requestBody = {
          text: text,
          model_id: "eleven_multilingual_v2", // Changed to multilingual for Hindi/English support
          voice_settings: {
            stability: 0.5,
            similarity_boost: 0.5,
          },
        };

        console.log("📤 ALEX DEBUG: Request body:", requestBody);
        console.log(
          "🌐 ALEX DEBUG: API URL:",
          `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`,
        );

        // Updated to match your curl command exactly
        const response = await fetch(
          `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "xi-api-key": apiKey,
            },
            body: JSON.stringify(requestBody),
          },
        );

        console.log(
          "📥 ALEX DEBUG: ElevenLabs response status:",
          response.status,
        );
        console.log(
          "📥 ALEX DEBUG: Response headers:",
          Object.fromEntries(response.headers.entries()),
        );

        if (!response.ok) {
          const errorText = await response.text();
          console.error(
            "❌ ALEX DEBUG: ElevenLabs API error details:",
            errorText,
          );
          console.error("❌ ALEX DEBUG: Full response:", {
            status: response.status,
            statusText: response.statusText,
            headers: Object.fromEntries(response.headers.entries()),
            body: errorText,
          });
          throw new Error(
            `ElevenLabs API error: ${response.status} - ${errorText}`,
          );
        }

        const audioBlob = await response.blob();
        console.log("🎵 ALEX DEBUG: Audio blob size:", audioBlob.size, "bytes");
        console.log("🎵 ALEX DEBUG: Audio blob type:", audioBlob.type);

        if (audioBlob.size === 0) {
          console.error("❌ ALEX DEBUG: Received empty audio blob");
          throw new Error("Received empty audio response from ElevenLabs");
        }

        const audioUrl = URL.createObjectURL(audioBlob);
        console.log(
          "🔗 ALEX DEBUG: Audio URL created:",
          audioUrl.substring(0, 50) + "...",
        );

        if (audioRef.current) {
          audioRef.current.src = audioUrl;
          console.log("▶️ ALEX DEBUG: Starting audio playback");

          // Add event listeners for debugging
          audioRef.current.onloadstart = () =>
            console.log("📡 ALEX DEBUG: Audio loading started");
          audioRef.current.oncanplay = () =>
            console.log("✅ ALEX DEBUG: Audio can play");
          audioRef.current.onplay = () =>
            console.log("🎵 ALEX DEBUG: Audio playback started");
          audioRef.current.onended = () => {
            console.log("🏁 ALEX DEBUG: Audio playback ended");
            setCurrentStatus("listening");
            URL.revokeObjectURL(audioUrl); // Clean up
          };
          audioRef.current.onerror = (error) => {
            console.error("❌ ALEX DEBUG: Audio playback error:", error);
            console.error("❌ ALEX DEBUG: Audio element error details:", {
              error: audioRef.current?.error,
              networkState: audioRef.current?.networkState,
              readyState: audioRef.current?.readyState,
              src: audioRef.current?.src,
            });
            setCurrentStatus("listening");
            URL.revokeObjectURL(audioUrl); // Clean up
          };

          try {
            // Set volume to maximum
            audioRef.current.volume = 1.0;
            await audioRef.current.play();
            console.log("✅ ALEX DEBUG: Audio play() succeeded");
          } catch (playError) {
            console.error("❌ ALEX DEBUG: Audio play() failed:", playError);
            console.error("❌ ALEX DEBUG: Play error details:", {
              name: playError.name,
              message: playError.message,
              code: playError.code,
            });
            setCurrentStatus("listening");
            URL.revokeObjectURL(audioUrl);
          }
        } else {
          console.error("❌ ALEX DEBUG: audioRef.current is null");
          URL.revokeObjectURL(audioUrl);
        }
      } catch (error) {
        console.error("❌ ALEX DEBUG: Error with text-to-speech:", error);
        console.error("❌ ALEX DEBUG: Full error details:", {
          name: error.name,
          message: error.message,
          stack: error.stack,
        });
        setCurrentStatus("listening");

        // Fallback to browser speech if ElevenLabs fails
        console.log("🔄 ALEX DEBUG: Falling back to browser speech synthesis");
        if ("speechSynthesis" in window) {
          const utterance = new SpeechSynthesisUtterance(text);
          utterance.rate = 0.9;
          utterance.pitch = 1;
          utterance.volume = 1;
          utterance.onend = () => setCurrentStatus("listening");
          window.speechSynthesis.speak(utterance);
        }
      }
    },
    [apiKey, voiceId],
  );

  const toggleListening = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  return (
    <div
      className="relative flex flex-col items-center"
      data-testid="ceo-node-v2"
    >
      {/* Audio element for TTS */}
      <audio
        ref={audioRef}
        onEnded={() => {
          console.log("🏁 ALEX DEBUG: Audio element onEnded triggered");
          if (currentStatus === "speaking") {
            setCurrentStatus("listening");
          }
        }}
        onError={(e) => {
          console.error("❌ ALEX DEBUG: Audio element error:", e);
          setCurrentStatus("listening");
        }}
        onLoadStart={() => console.log("📡 ALEX DEBUG: Audio loadstart event")}
        onCanPlay={() => console.log("✅ ALEX DEBUG: Audio canplay event")}
        onPlay={() => console.log("🎵 ALEX DEBUG: Audio play event")}
        style={{ display: "none" }}
        preload="auto"
        controls={false}
      />

      {/* Pulse rings when active */}
      {isActive && (
        <>
          <span
            className="pulse-ring absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-32 w-32 rounded-full border"
            style={{ borderColor: color, opacity: 0.6 }}
          />
          <span
            className="pulse-ring absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-32 w-32 rounded-full border"
            style={{ borderColor: color, opacity: 0.4, animationDelay: "0.4s" }}
          />
        </>
      )}

      <motion.div
        animate={isActive ? { scale: [1, 1.04, 1] } : { scale: 1 }}
        transition={{ duration: 1.6, repeat: isActive ? Infinity : 0 }}
        className="relative h-32 w-32 rounded-2xl overflow-hidden flex items-center justify-center cursor-pointer"
        onClick={toggleListening}
        style={{
          background:
            "linear-gradient(135deg, rgba(0,240,255,0.15), rgba(255,0,255,0.08))",
          border: `1.5px solid ${color}`,
          boxShadow: isActive
            ? `0 0 40px ${color}55, inset 0 0 30px ${color}22`
            : `0 0 20px ${color}33`,
        }}
      >
        <img
          src="https://images.unsplash.com/photo-1677212004257-103cfa6b59d0?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjY2NzZ8MHwxfHNlYXJjaHw0fHxyb2JvdCUyMGZhY2UlMjBwcm9maWxlJTIwbmVvbnxlbnwwfHx8fDE3NzczNDk0MjV8MA&ixlib=rb-4.1.0&q=85"
          alt="CEO Agent v2"
          className="absolute inset-0 h-full w-full object-cover opacity-60 mix-blend-luminosity"
        />
        <div
          className="absolute inset-0"
          style={{
            background: `linear-gradient(180deg, transparent, ${color}22)`,
          }}
        />

        {/* Voice status icon */}
        <div className="relative z-10 flex items-center justify-center">
          {currentStatus === "listening" && (
            <Mic className="h-8 w-8" style={{ color }} />
          )}
          {currentStatus === "speaking" && (
            <Volume2 className="h-8 w-8" style={{ color }} />
          )}
          {currentStatus === "idle" && (
            <MicOff className="h-6 w-6" style={{ color: "#666" }} />
          )}
          {(currentStatus === "processing" ||
            currentStatus === "thinking" ||
            currentStatus === "routing") && (
            <Crown className="h-8 w-8" style={{ color }} />
          )}
        </div>
      </motion.div>

      <div className="mt-4 text-center">
        <div className="font-display text-lg tracking-tight">CEO Agent v2</div>
        <div
          className="font-mono text-[10px] uppercase tracking-[0.25em] mt-1 flex items-center justify-center gap-2"
          style={{ color }}
        >
          <span
            className="h-1.5 w-1.5 rounded-full"
            style={{ background: color, boxShadow: `0 0 8px ${color}` }}
          />
          {STATUS_LABEL[currentStatus]}
        </div>

        {/* Show current transcript when listening */}
        {isWakeWordDetected && transcript && (
          <div className="mt-2 text-xs text-gray-400 max-w-xs truncate">
            "{transcript}"
          </div>
        )}

        {/* Instructions */}
        {!isWakeWordDetected && (
          <div className="mt-2 text-xs text-gray-500">
            Say "Alex" to wake up
          </div>
        )}

        {/* Show conversation state */}
        {awaitingConfirmation && (
          <div className="mt-2 text-xs text-yellow-400">
            Waiting for confirmation...
          </div>
        )}

        {conversationState === "listening_for_task" && (
          <div className="mt-2 text-xs text-green-400">Ready to help!</div>
        )}
      </div>
    </div>
  );
}
