import * as Icons from "lucide-react";
import { Lock } from "lucide-react";

export default function LockedTeam({ team }) {
  const Icon = Icons[team.icon] || Icons.Layers;
  return (
    <div
      className="relative rounded-xl p-5 border border-dashed border-slate-700/70 bg-[#0f1422]/50 backdrop-blur-sm flex items-center gap-4 opacity-60 hover:opacity-80 transition"
      data-testid={`locked-team-${team.id}`}
    >
      <div className="h-10 w-10 rounded-lg flex items-center justify-center bg-slate-800/60">
        <Icon className="h-4 w-4 text-slate-400" />
      </div>
      <div className="flex-1">
        <div className="font-display text-sm tracking-tight text-slate-300">{team.name} Team</div>
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500 mt-1">{team.tagline}</div>
      </div>
      <Lock className="h-4 w-4 text-slate-500" />
    </div>
  );
}
