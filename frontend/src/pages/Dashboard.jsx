import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  fetchTeams,
  orchestrate,
  getOrchestrationPlan,
  executeAgent,
} from "../lib/api";
import FlowVisibility from "../components/FlowVisibility";
import { useAgentActions } from "../store/agentStore";
import CEONode from "../components/CEONode";
import CEONodev2 from "../components/CEONodev2";
import CEOChatInterface from "../components/CEOChatInterface";
import AgentNode from "../components/AgentNode";
import TeamSection from "../components/TeamSection";
import ConnectionLines from "../components/ConnectionLines";
import TerminalFeed from "../components/TerminalFeed";
import ActivityFlowTabs from "../components/ActivityFlowTabs";
import CommandBar from "../components/CommandBar";
import OutputDialog from "../components/OutputDialog";
import { Activity, Sparkles, ToggleLeft, ToggleRight } from "lucide-react";
import { toast } from "sonner";

const QUICK_TASKS = [
  {
    label: "Launch a product",
    prompt:
      "Plan the launch of our new AI agent platform: research the audience, write the launch announcement, and publish it on LinkedIn and Twitter.",
  },
  {
    label: "Ship a landing page",
    prompt:
      "Design and ship a new landing page hero section with parallax animation. Include SEO meta updates.",
    agent_id: "frontend_engineer",
  },
  {
    label: "Close a deal",
    prompt:
      "Find a Series A SaaS prospect, draft an outreach email, and prep the demo deck.",
    agent_id: null,
  },
  {
    label: "Draft a PRD",
    prompt:
      "Draft a PRD for multi-team orchestration v2 — include user stories and a phased roadmap.",
    agent_id: "pm_agent",
  },
  {
    label: "SEO audit",
    prompt:
      "Run a full on-page SEO audit on the landing page and propose meta + content fixes.",
    agent_id: "seo_specialist",
  },
  {
    label: "Weekly report",
    prompt:
      "Generate this week's marketing analytics report with funnel insights.",
    agent_id: "analytics_agent",
  },
];

export default function Dashboard() {
  const [teamsData, setTeamsData] = useState({ teams: [], locked_teams: [] });
  const [ceoStatus, setCeoStatus] = useState("idle");
  const [activeAgentId, setActiveAgentId] = useState(null);
  const [agentStatuses, setAgentStatuses] = useState({});
  const [useVoiceMode, setUseVoiceMode] = useState(false);
  const [showCEOChat, setShowCEOChat] = useState(false);
  const [initialChatMessage, setInitialChatMessage] = useState("");
  const [logs, setLogs] = useState([
    {
      actor: "SYSTEM",
      message: "AI Startup OS online. 4 teams active, 20 agents ready.",
      status: "info",
      timestamp: new Date().toISOString(),
    },
    {
      actor: "CEO",
      message: "Standing by for your directives.",
      status: "info",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [outputs, setOutputs] = useState([]);
  const [openOutput, setOpenOutput] = useState(null);
  const [running, setRunning] = useState(false);

  const canvasRef = useRef(null);

  useEffect(() => {
    fetchTeams()
      .then((data) => setTeamsData(data))
      .catch((err) => {
        console.error(err);
        toast.error("Failed to load org structure");
      });
  }, []);

  const pushLog = (entry) => {
    setLogs((prev) => [
      ...prev,
      { ...entry, timestamp: entry.timestamp || new Date().toISOString() },
    ]);
  };

  const handleVoiceTask = async (task) => {
    // Handle voice-based task from CEONodev2
    await runTask({ task });
  };

  const runTask = async ({ task, agent_id = null }) => {
    if (running) {
      toast.warning("CEO is busy. Please wait.");
      return;
    }
    if (!task?.trim()) return;

    // Open CEO chat interface instead of directly processing
    setShowCEOChat(true);
    setInitialChatMessage(task);
  };

  const handleChatRequirementsFinalized = async ({
    requirements,
    plan,
    orchestrationResult,
    conversationId,
  }) => {
    // Add detailed logging for debugging
    console.log("[CEO_DEBUG] handleChatRequirementsFinalized called");
    console.log("[CEO_DEBUG] Requirements:", requirements);
    console.log("[CEO_DEBUG] Plan:", plan);
    console.log("[CEO_DEBUG] OrchestrationResult:", orchestrationResult);
    console.log("[CEO_DEBUG] ConversationId:", conversationId);

    // Close the chat interface
    setShowCEOChat(false);
    setRunning(true);
    setCeoStatus("thinking");

    pushLog({
      actor: "USER",
      message: requirements.original_task || "Task submitted via chat",
      status: "info",
    });
    pushLog({
      actor: "CEO",
      message: "Requirements gathered. Processing plan…",
      status: "thinking",
    });

    try {
      await new Promise((r) => setTimeout(r, 700));

      // Check if we have orchestration result from backend
      let orchestrationPlan = null;
      console.log(
        "[CEO_DEBUG] Checking orchestrationResult:",
        orchestrationResult,
      );
      console.log(
        "[CEO_DEBUG] orchestrationResult type:",
        typeof orchestrationResult,
      );
      console.log(
        "[CEO_DEBUG] orchestrationResult keys:",
        orchestrationResult ? Object.keys(orchestrationResult) : "null",
      );

      if (orchestrationResult && !orchestrationResult.error) {
        orchestrationPlan = orchestrationResult;
        pushLog({
          actor: "CEO",
          message: "Orchestration plan received from backend",
          status: "info",
        });
      } else if (orchestrationResult && orchestrationResult.error) {
        pushLog({
          actor: "CEO",
          message: `Orchestration error: ${orchestrationResult.error}`,
          status: "error",
        });
      } else {
        console.log(
          "[CEO_DEBUG] No orchestration result or result is null/undefined",
        );
      }

      // Use orchestration plan if available, otherwise fall back to the plan from requirements
      const finalPlan = orchestrationPlan || plan || {};
      const steps = finalPlan.steps || [];

      console.log("[CEO_DEBUG] orchestrationPlan:", orchestrationPlan);
      console.log("[CEO_DEBUG] plan from requirements:", plan);
      console.log("[CEO_DEBUG] finalPlan selected:", finalPlan);
      console.log("[CEO_DEBUG] steps extracted:", steps);

      // Add detailed logging for debugging
      console.log("[CEO_DEBUG] Final Plan:", finalPlan);
      console.log(
        "[CEO_DEBUG] Plan mode:",
        finalPlan.mode || plan.mode || "UNDEFINED",
      );
      console.log("[CEO_DEBUG] Plan steps:", steps);
      console.log("[CEO_DEBUG] Number of agents:", steps.length || 1);
      console.log(
        "[CEO_DEBUG] Plan rationale:",
        finalPlan.rationale || plan.rationale || "UNDEFINED",
      );

      pushLog({
        actor: "CEO",
        message: `Plan ready · mode=${finalPlan.mode || plan.mode || "undefined"} · ${steps.length || 1} agent(s) · ${finalPlan.rationale || plan.rationale || "undefined"}`,
        status: "info",
      });

      // CEO is now routing
      setCeoStatus("routing");

      const agentResults = [];
      const finalAgentRuns = [];

      // Step 2: Execute each agent individually with CEO-mediated workflow
      for (let i = 0; i < steps.length; i++) {
        const step = steps[i];

        // Log handoff to agent
        pushLog({
          actor: "CEO",
          message: `→ Handing off to ${step.agent_name} (${step.team_name}): ${step.instruction}`,
          status: "info",
        });

        // Activate agent UI
        setActiveAgentId(step.agent_id);
        setAgentStatuses((prev) => ({
          ...prev,
          [step.agent_id]: "working",
        }));

        // Log agent acknowledgment
        pushLog({
          actor: step.agent_name,
          message: "Acknowledged. Working on it…",
          status: "working",
        });

        // Smooth-scroll the active agent into view
        const el = document.querySelector(
          `[data-testid="agent-card-${step.agent_id}"]`,
        );
        if (el && el.scrollIntoView) {
          el.scrollIntoView({ behavior: "smooth", block: "center" });
        }

        try {
          // Execute individual agent through its endpoint
          const agentResult = await executeAgent(step.agent_id, {
            task: step.instruction,
            context:
              agentResults.length > 0 ? JSON.stringify(agentResults) : null,
            metadata: {
              orchestration_request_id: plan.request_id,
              step_number: i + 1,
              total_steps: steps.length,
            },
          });

          // Log agent completion and return to CEO
          pushLog({
            actor: step.agent_name,
            message: "Task completed. Returning output to CEO for analysis.",
            status: "success",
          });

          // CEO receives and analyzes the agent response
          setCeoStatus("working");
          pushLog({
            actor: "CEO",
            message: `← Received output from ${step.agent_name}. Analyzing results...`,
            status: "working",
          });

          // CEO processing delay for visual effect
          await new Promise((r) => setTimeout(r, 1200));

          // CEO analyzes and processes the output
          pushLog({
            actor: "CEO",
            message: `Analysis complete. ${i < steps.length - 1 ? "Preparing delegation to next agent." : "All tasks completed successfully."}`,
            status: "info",
          });

          agentResults.push(agentResult);

          // Create agent run object for compatibility
          const agentRun = {
            agent_id: step.agent_id,
            agent_name: step.agent_name,
            team_id: step.team_id,
            team_name: step.team_name,
            instruction: step.instruction,
            output: agentResult.output,
            success: agentResult.success,
            duration_ms: agentResult.duration_ms,
          };

          finalAgentRuns.push(agentRun);

          // Mark agent as done
          setAgentStatuses((prev) => ({
            ...prev,
            [step.agent_id]: "done",
          }));

          // If there's a next step, CEO prepares for next delegation
          if (i < steps.length - 1) {
            setCeoStatus("working");
            pushLog({
              actor: "CEO",
              message: `Extracting relevant content for ${steps[i + 1].agent_name}...`,
              status: "working",
            });
            await new Promise((r) => setTimeout(r, 800));

            // CEO transitions to routing mode for delegation
            setCeoStatus("routing");
            pushLog({
              actor: "CEO",
              message: `Ready to delegate to ${steps[i + 1].agent_name}...`,
              status: "routing",
            });
            await new Promise((r) => setTimeout(r, 300));
          }

          // Small delay for visual effect
          await new Promise((r) => setTimeout(r, 300));
        } catch (agentError) {
          console.error(`Agent ${step.agent_name} failed:`, agentError);

          // Log agent failure
          pushLog({
            actor: step.agent_name,
            message: `Error: ${agentError.message}. Reporting failure to CEO.`,
            status: "error",
          });

          // CEO handles the failure
          setCeoStatus("working");
          pushLog({
            actor: "CEO",
            message: `← Agent ${step.agent_name} reported failure. Analyzing error and determining next steps...`,
            status: "error",
          });

          await new Promise((r) => setTimeout(r, 800));

          // Create failed agent run
          const failedRun = {
            agent_id: step.agent_id,
            agent_name: step.agent_name,
            team_id: step.team_id,
            team_name: step.team_name,
            instruction: step.instruction,
            output: `Execution failed: ${agentError.message}`,
            success: false,
            error: agentError.message,
          };

          finalAgentRuns.push(failedRun);
          agentResults.push({ error: agentError.message });

          // Mark agent as failed
          setAgentStatuses((prev) => ({
            ...prev,
            [step.agent_id]: "error",
          }));
        }
      }

      // Final CEO analysis and completion
      setCeoStatus("working");
      pushLog({
        actor: "CEO",
        message: "All agents have reported back. Conducting final analysis...",
        status: "working",
      });

      await new Promise((r) => setTimeout(r, 1000));

      pushLog({
        actor: "CEO",
        message: "Final analysis complete. Mission accomplished successfully.",
        status: "success",
      });

      // Final state
      setCeoStatus("done");

      // Determine final output from last successful agent
      const lastSuccessfulResult = agentResults.filter((r) => !r.error).pop();
      const finalOutput =
        lastSuccessfulResult?.output || "Task completed with some failures";

      const output = {
        id: plan.request_id,
        task: plan.task,
        mode: plan.mode,
        rationale: plan.rationale,
        agent_runs: finalAgentRuns,
        used_llm: true,
        // Backwards-compat fields for displays
        agent_id: plan.chosen_agent_id,
        agent_name: plan.chosen_agent_name,
        team_name: plan.team_name,
        output: finalOutput,
        timestamp: new Date().toISOString(),
      };

      setOutputs((prev) => [output, ...prev]);
      setOpenOutput(output);

      const planLabel =
        finalAgentRuns.length > 1
          ? `${finalAgentRuns.length} agents collaborated`
          : `${plan.chosen_agent_name} delivered`;
      toast.success(planLabel);

      // Clean up after a beat
      setTimeout(() => {
        setActiveAgentId(null);
        setCeoStatus("idle");
        setAgentStatuses((prev) => {
          const next = { ...prev };
          finalAgentRuns.forEach((r) => {
            next[r.agent_id] = "idle";
          });
          return next;
        });
        setRunning(false);
      }, 2200);
    } catch (err) {
      console.error(err);
      toast.error("Orchestration failed");
      pushLog({
        actor: "SYSTEM",
        message: "Error: orchestration failed.",
        status: "info",
      });
      setCeoStatus("idle");
      setActiveAgentId(null);
      setRunning(false);
    }
  };

  const teams = teamsData.teams || [];
  const totalAgents = teams.reduce(
    (acc, t) => acc + (t.agents?.length || 0),
    0,
  );

  return (
    <div
      className="relative min-h-screen w-full text-white"
      data-testid="dashboard-root"
    >
      <div className="fixed inset-0 bg-grid opacity-50 pointer-events-none" />
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(900px at 20% 10%, rgba(0,240,255,0.08), transparent), radial-gradient(900px at 80% 90%, rgba(255,0,255,0.06), transparent)",
        }}
      />

      <header
        className="relative z-20 flex items-center justify-between px-8 py-5 border-b border-white/5 backdrop-blur-md bg-black/20"
        data-testid="app-header"
      >
        <div className="flex items-center gap-3">
          <div
            className="relative h-10 w-10 rounded-lg flex items-center justify-center"
            style={{
              background:
                "linear-gradient(135deg, rgba(0,240,255,0.2), rgba(255,0,255,0.15))",
              border: "1px solid rgba(0,240,255,0.4)",
            }}
          >
            <Sparkles className="h-5 w-5 text-cyan-300" />
          </div>
          <div>
            <div className="font-display text-xl tracking-tight">
              Startup<span className="text-cyan-300">.AI</span>
            </div>
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-400">
              AI Automation Startup System · Phase 1
            </div>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <div className="hidden md:flex items-center gap-2 text-xs font-mono text-slate-400">
            <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(0,255,136,0.8)]" />
            <span>
              {teams.length} TEAMS · {totalAgents} AGENTS
            </span>
          </div>
          <div className="hidden md:flex items-center gap-2 text-xs font-mono text-slate-400">
            <Activity className="h-3.5 w-3.5 text-cyan-300" />
            <span>
              {outputs.length} TASK{outputs.length === 1 ? "" : "S"} COMPLETED
            </span>
          </div>
          <button
            onClick={() => setUseVoiceMode(!useVoiceMode)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 transition-colors text-xs font-mono"
            title={
              useVoiceMode ? "Switch to Text Mode" : "Switch to Voice Mode"
            }
          >
            {useVoiceMode ? (
              <ToggleRight className="h-4 w-4 text-cyan-300" />
            ) : (
              <ToggleLeft className="h-4 w-4 text-slate-400" />
            )}
            <span className={useVoiceMode ? "text-cyan-300" : "text-slate-400"}>
              VOICE {useVoiceMode ? "ON" : "OFF"}
            </span>
          </button>
        </div>
      </header>

      <main className="relative z-10 grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-0 min-h-[calc(100vh-72px)]">
        <section
          ref={canvasRef}
          className="relative px-6 lg:px-12 pt-10 pb-[22rem] overflow-hidden"
          data-testid="org-canvas"
        >
          <div className="mb-10">
            <div className="font-mono text-[11px] uppercase tracking-[0.3em] text-cyan-300/80 mb-2 flex items-center gap-2">
              // org · live · phase 1
              <span className="px-1.5 py-0.5 rounded bg-fuchsia-400/10 border border-fuchsia-400/30 text-fuchsia-300 text-[9px]">
                CEO · CLAUDE SONNET 4.5
              </span>
            </div>
            <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-light leading-[0.95]">
              Your AI <span className="text-cyan-300">startup</span>,<br />
              orchestrated in{" "}
              <span className="italic text-fuchsia-300">real time</span>.
            </h1>
            <p className="text-slate-400 mt-3 max-w-xl text-sm">
              The CEO consults Claude to assemble a multi-agent plan across{" "}
              {totalAgents} specialists in {teams.length} teams. One directive.
              Many agents. Real coordination.
            </p>
          </div>

          <div className="flex flex-col items-center relative">
            {useVoiceMode ? (
              <CEONodev2 status={ceoStatus} onTaskReceived={handleVoiceTask} />
            ) : (
              <CEONode status={ceoStatus} />
            )}

            <div className="mt-12 w-full space-y-12" data-testid="teams-stack">
              {teams.map((team, idx) => (
                <TeamSection
                  key={team.id}
                  team={team}
                  index={idx}
                  agentStatuses={agentStatuses}
                  activeAgentId={activeAgentId}
                  onAgentClick={(agent) => {
                    const last = outputs.find((o) => o.agent_id === agent.id);
                    if (last) setOpenOutput(last);
                  }}
                  AgentNode={AgentNode}
                />
              ))}
            </div>
          </div>

          <ConnectionLines
            activeAgentId={activeAgentId}
            canvasRef={canvasRef}
          />
        </section>

        <aside
          className="relative border-l border-white/5 bg-[#0B0F19]/80 backdrop-blur-md"
          data-testid="terminal-aside"
        >
          <ActivityFlowTabs logs={logs} />
        </aside>
      </main>

      {!useVoiceMode && (
        <CommandBar
          onSubmit={runTask}
          running={running}
          quickTasks={QUICK_TASKS}
        />
      )}

      <AnimatePresence>
        {openOutput && (
          <OutputDialog
            output={openOutput}
            onClose={() => setOpenOutput(null)}
          />
        )}
      </AnimatePresence>

      {/* CEO Chat Interface */}
      {showCEOChat && (
        <CEOChatInterface
          onClose={() => {
            setShowCEOChat(false);
            setInitialChatMessage("");
          }}
          onRequirementsFinalized={handleChatRequirementsFinalized}
          initialMessage={initialChatMessage}
        />
      )}

      {/* Flow Visibility Dashboard is now integrated in the sidebar tabs */}
    </div>
  );
}
