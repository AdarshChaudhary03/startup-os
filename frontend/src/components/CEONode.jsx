import { motion } from "framer-motion";
import { Crown } from "lucide-react";

const STATUS_LABEL = {
  idle: "STANDING BY",
  thinking: "THINKING…",
  routing: "ROUTING TASK",
  done: "TASK COMPLETE",
};

const STATUS_COLOR = {
  idle: "#3A4B6E",
  thinking: "#00F0FF",
  routing: "#FF00FF",
  done: "#00FF88",
};

export default function CEONode({ status = "idle" }) {
  const color = STATUS_COLOR[status];
  const isActive = status !== "idle";

  return (
    <div className="relative flex flex-col items-center" data-testid="ceo-node">
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
        className="relative h-32 w-32 rounded-2xl overflow-hidden flex items-center justify-center"
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
          alt="CEO Agent"
          className="absolute inset-0 h-full w-full object-cover opacity-60 mix-blend-luminosity"
        />
        <div
          className="absolute inset-0"
          style={{
            background: `linear-gradient(180deg, transparent, ${color}22)`,
          }}
        />
        {/* <Crown className="relative z-10 h-10 w-10" style={{ color }} /> */}
      </motion.div>

      <div className="mt-4 text-center">
        <div className="font-display text-lg tracking-tight">CEO Agent</div>
        <div
          className="font-mono text-[10px] uppercase tracking-[0.25em] mt-1 flex items-center justify-center gap-2"
          style={{ color }}
        >
          <span
            className="h-1.5 w-1.5 rounded-full"
            style={{ background: color, boxShadow: `0 0 8px ${color}` }}
          />
          {STATUS_LABEL[status]}
        </div>
      </div>
    </div>
  );
}
