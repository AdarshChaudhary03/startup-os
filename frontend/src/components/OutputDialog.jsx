import { motion } from "framer-motion";
import { X, CheckCircle2, GitBranch, Zap, Target, Sparkles } from "lucide-react";

const MODE_META = {
  single: { label: "Single agent", icon: Target, color: "#00F0FF" },
  sequential: { label: "Sequential pipeline", icon: GitBranch, color: "#FF00FF" },
  parallel: { label: "Parallel execution", icon: Zap, color: "#00FF88" },
};

export default function OutputDialog({ output, onClose }) {
  const runs = output.agent_runs && output.agent_runs.length > 0
    ? output.agent_runs
    : [{
        agent_id: output.agent_id,
        agent_name: output.agent_name,
        team_name: output.team_name,
        instruction: output.task,
        output: output.output,
      }];
  const mode = output.mode || "single";
  const meta = MODE_META[mode] || MODE_META.single;
  const ModeIcon = meta.icon;
  const usedLLM = output.used_llm;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-6"
      data-testid="output-dialog"
    >
      <div className="absolute inset-0 bg-black/75 backdrop-blur-sm" onClick={onClose} />
      <motion.div
        initial={{ y: 30, opacity: 0, scale: 0.96 }}
        animate={{ y: 0, opacity: 1, scale: 1 }}
        exit={{ y: 30, opacity: 0, scale: 0.96 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
        className="relative w-full max-w-3xl rounded-2xl overflow-hidden max-h-[85vh] flex flex-col"
        style={{
          background: "linear-gradient(160deg, rgba(18, 24, 38, 0.97), rgba(11, 15, 25, 0.99))",
          border: "1px solid rgba(0, 240, 255, 0.3)",
          boxShadow: "0 0 60px rgba(0, 240, 255, 0.18)",
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 shrink-0">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="h-5 w-5 text-emerald-400" />
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-emerald-300">delivered</div>
              <div className="font-display text-base flex items-center gap-2">
                {runs.length === 1 ? runs[0].agent_name : `${runs.length}-Agent Plan`}
                <span className="font-mono text-[10px] uppercase tracking-[0.2em] px-2 py-0.5 rounded" style={{ background: `${meta.color}15`, color: meta.color, border: `1px solid ${meta.color}40` }}>
                  <ModeIcon className="inline h-3 w-3 mr-1" />{meta.label}
                </span>
              </div>
            </div>
          </div>
          <button onClick={onClose} className="h-8 w-8 rounded-lg hover:bg-white/5 flex items-center justify-center transition" data-testid="output-close">
            <X className="h-4 w-4 text-slate-400" />
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto px-6 py-5 space-y-5">
          {/* Directive */}
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500 mb-1">// directive</div>
            <div className="text-sm text-slate-300 italic">"{output.task}"</div>
          </div>

          {/* CEO Rationale */}
          {output.rationale && (
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-fuchsia-300 mb-1 flex items-center gap-1">
                <Sparkles className="h-3 w-3" />
                ceo · rationale
                {usedLLM && <span className="ml-2 px-1.5 py-0.5 rounded text-[9px] tracking-wider bg-fuchsia-400/10 border border-fuchsia-400/30">claude · sonnet 4.5</span>}
              </div>
              <div className="text-sm text-slate-300">{output.rationale}</div>
            </div>
          )}

          {/* Agent runs */}
          <div className="space-y-3">
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-cyan-300">// outputs</div>
            {runs.map((run, idx) => (
              <div key={`${run.agent_id}-${idx}`} className="rounded-lg overflow-hidden" style={{ background: "rgba(0, 240, 255, 0.04)", border: "1px solid rgba(0, 240, 255, 0.18)" }} data-testid={`output-run-${idx}`}>
                <div className="px-4 py-2.5 flex items-center gap-3 border-b border-white/5" style={{ background: "rgba(0, 240, 255, 0.06)" }}>
                  <span className="h-6 w-6 rounded flex items-center justify-center font-mono text-[10px] text-cyan-300" style={{ background: "rgba(0, 240, 255, 0.12)", border: "1px solid rgba(0, 240, 255, 0.3)" }}>
                    {idx + 1}
                  </span>
                  <div className="flex-1">
                    <div className="font-display text-sm">{run.agent_name}</div>
                    <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-slate-500">{run.team_name}</div>
                  </div>
                </div>
                {run.instruction && (
                  <div className="px-4 pt-3">
                    <div className="font-mono text-[9px] uppercase tracking-[0.25em] text-slate-500 mb-1">instruction</div>
                    <div className="text-xs text-slate-400 italic">"{run.instruction}"</div>
                  </div>
                )}
                <div className="px-4 py-3">
                  <div className="font-mono text-[9px] uppercase tracking-[0.25em] text-emerald-300/70 mb-1">output</div>
                  <div className="text-sm text-white leading-relaxed">{run.output}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-white/5 font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500 flex items-center justify-between shrink-0">
          <span>request_id · {output.id?.slice(0, 8)}</span>
          <span>{new Date(output.timestamp).toLocaleTimeString()}</span>
        </div>
      </motion.div>
    </motion.div>
  );
}
