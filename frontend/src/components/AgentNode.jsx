import { motion } from "framer-motion";
import * as Icons from "lucide-react";

const STATUS_LABEL = {
  idle: "IDLE",
  working: "WORKING",
  done: "DELIVERED",
};

export default function AgentNode({ agent, status = "idle", isActive, onClick }) {
  const Icon = Icons[agent.icon] || Icons.Bot;

  const color = isActive ? agent.color : status === "done" ? "#00FF88" : "rgba(58, 75, 110, 0.6)";
  const borderColor = isActive ? agent.color : "rgba(0, 240, 255, 0.15)";

  return (
    <button
      onClick={onClick}
      className="group relative w-full text-left"
      data-testid={`agent-card-${agent.id}`}
    >
      {/* pulse rings while working */}
      {isActive && (
        <>
          <span className="pulse-ring absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-24 w-24 rounded-full border" style={{ borderColor: agent.color }} />
        </>
      )}

      <motion.div
        whileHover={{ y: -4 }}
        transition={{ type: "spring", stiffness: 300, damping: 22 }}
        className="relative rounded-xl p-4 backdrop-blur-md transition-colors"
        style={{
          background: isActive
            ? `linear-gradient(160deg, ${agent.color}18, rgba(18, 24, 38, 0.85))`
            : "rgba(18, 24, 38, 0.7)",
          border: `1px solid ${borderColor}`,
          boxShadow: isActive ? `0 0 24px ${agent.color}55` : "none",
        }}
      >
        {/* status dot */}
        <div className="flex items-center justify-between mb-3">
          <div className="h-9 w-9 rounded-lg flex items-center justify-center" style={{ background: `${agent.color}22`, border: `1px solid ${agent.color}55` }}>
            <Icon className="h-4 w-4" style={{ color: agent.color }} />
          </div>
          <span className="h-2 w-2 rounded-full" style={{ background: color, boxShadow: isActive ? `0 0 10px ${agent.color}` : "none" }} />
        </div>

        <div className="font-display text-sm leading-tight mb-1">{agent.name}</div>
        <div className="text-xs text-slate-400 leading-snug min-h-[32px]">{agent.role}</div>

        <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between">
          <span className="font-mono text-[9px] uppercase tracking-[0.2em]" style={{ color: isActive ? agent.color : "#64748B" }}>
            {STATUS_LABEL[status]}
          </span>
          {/* Working bar */}
          {isActive && (
            <span className="relative w-10 h-[2px] bg-white/5 overflow-hidden rounded">
              <motion.span
                className="absolute inset-y-0 left-0 w-1/2"
                style={{ background: agent.color }}
                animate={{ x: ["-100%", "200%"] }}
                transition={{ duration: 1.2, repeat: Infinity, ease: "linear" }}
              />
            </span>
          )}
        </div>
      </motion.div>
    </button>
  );
}
