import { motion } from "framer-motion";
import * as Icons from "lucide-react";

export default function TeamSection({ team, index, agentStatuses, activeAgentId, onAgentClick, AgentNode }) {
  const Icon = Icons[team.icon] || Icons.Layers;
  const teamActive = team.agents.some((a) => a.id === activeAgentId);

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 + index * 0.08 }}
      className="w-full"
      data-testid={`team-section-${team.id}`}
    >
      {/* Team header */}
      <div className="flex items-center gap-3 mb-5 px-1">
        <span className="h-px flex-1" style={{ background: `linear-gradient(to right, transparent, ${team.color}55, transparent)` }} />
        <div className="flex items-center gap-2.5 px-3 py-1.5 rounded-full" style={{ background: `${team.color}10`, border: `1px solid ${team.color}33` }}>
          <Icon className="h-3.5 w-3.5" style={{ color: team.color }} />
          <span className="font-mono text-[11px] uppercase tracking-[0.3em]" style={{ color: team.color }}>
            {team.name} Team
          </span>
          <span className="font-mono text-[9px] tracking-wider text-slate-500">· {team.tagline}</span>
          {teamActive && (
            <span className="ml-1 h-1.5 w-1.5 rounded-full" style={{ background: team.color, boxShadow: `0 0 8px ${team.color}` }} />
          )}
        </div>
        <span className="h-px flex-1" style={{ background: `linear-gradient(to left, transparent, ${team.color}55, transparent)` }} />
      </div>

      {/* Agent grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        {team.agents.map((agent, i) => (
          <motion.div
            key={agent.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.15 + index * 0.08 + i * 0.04 }}
          >
            <AgentNode
              agent={agent}
              status={agentStatuses[agent.id] || "idle"}
              isActive={activeAgentId === agent.id}
              onClick={() => onAgentClick(agent)}
            />
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
