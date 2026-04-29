import { useEffect, useRef } from "react";
import { Terminal } from "lucide-react";

const STATUS_COLOR = {
  info: "#94A3B8",
  thinking: "#00F0FF",
  working: "#FFB800",
  success: "#00FF88",
};

const ACTOR_COLOR = {
  USER: "#FFFFFF",
  CEO: "#FF00FF",
  SYSTEM: "#94A3B8",
};

export default function TerminalFeed({ logs }) {
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [logs]);

  return (
    <div className="h-full flex flex-col" data-testid="terminal-feed">
      <div className="flex items-center gap-2 px-5 py-4 border-b border-white/5">
        <Terminal className="h-4 w-4 text-cyan-300" />
        <div className="font-mono text-[11px] uppercase tracking-[0.3em] text-cyan-300">live · activity_stream</div>
        <div className="ml-auto flex gap-1">
          <span className="h-2 w-2 rounded-full bg-rose-500/60" />
          <span className="h-2 w-2 rounded-full bg-amber-400/60" />
          <span className="h-2 w-2 rounded-full bg-emerald-400/60" />
        </div>
      </div>
      <div ref={ref} className="flex-1 overflow-y-auto px-5 py-4 font-mono text-xs space-y-2.5 leading-relaxed">
        {logs.map((l, idx) => {
          const actorColor = ACTOR_COLOR[l.actor] || "#A78BFA";
          const dot = STATUS_COLOR[l.status] || "#94A3B8";
          const time = new Date(l.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
          return (
            <div key={idx} className="flex gap-3 group" data-testid={`log-line-${idx}`}>
              <span className="text-slate-600 text-[10px] mt-0.5 select-none">{time}</span>
              <span className="h-1.5 w-1.5 rounded-full mt-1.5 shrink-0" style={{ background: dot, boxShadow: `0 0 6px ${dot}88` }} />
              <div className="flex-1 break-words">
                <span className="font-semibold mr-2" style={{ color: actorColor }}>{l.actor}</span>
                <span className="text-slate-300">{l.message}</span>
              </div>
            </div>
          );
        })}
        <div className="flex gap-2 items-center text-cyan-300">
          <span>&gt;</span><span className="caret inline-block h-3 w-2 bg-cyan-300" />
        </div>
      </div>
    </div>
  );
}
