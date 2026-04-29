import { useState } from "react";
import { motion } from "framer-motion";
import { Send, Loader2 } from "lucide-react";

export default function CommandBar({ onSubmit, running, quickTasks }) {
  const [value, setValue] = useState("");

  const submit = (task, agent_id = null) => {
    if (!task?.trim() || running) return;
    onSubmit({ task, agent_id });
    setValue("");
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 lg:right-[380px] z-30 px-6 lg:px-12 pb-6 pt-3 pointer-events-none" data-testid="command-bar">
      <div className="pointer-events-auto max-w-4xl mx-auto">
        {/* Quick task chips */}
        <div className="flex flex-wrap gap-2 mb-3">
          {quickTasks.map((qt) => (
            <button
              key={qt.label}
              onClick={() => submit(qt.prompt, qt.agent_id)}
              disabled={running}
              data-testid={`quick-task-${qt.label.toLowerCase().replace(/\s+/g, "-")}`}
              className="px-3 py-1.5 text-xs font-mono uppercase tracking-wider rounded-full border border-cyan-500/20 text-cyan-200/90 bg-[#121826]/80 backdrop-blur-md hover:border-cyan-400/60 hover:bg-cyan-500/10 hover:text-cyan-100 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {qt.label}
            </button>
          ))}
        </div>

        {/* Input */}
        <motion.form
          initial={{ y: 30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.4 }}
          onSubmit={(e) => { e.preventDefault(); submit(value); }}
          className="relative flex items-center gap-3 rounded-2xl px-4 py-3 backdrop-blur-xl"
          style={{
            background: "rgba(11, 15, 25, 0.85)",
            border: "1px solid rgba(0, 240, 255, 0.25)",
            boxShadow: "0 0 40px rgba(0, 240, 255, 0.08), inset 0 0 20px rgba(0, 240, 255, 0.03)",
          }}
        >
          <span className="font-mono text-cyan-300 text-sm select-none">CEO &gt;</span>
          <input
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder='Hey CEO, write a tweet announcing our launch…'
            disabled={running}
            data-testid="command-input"
            className="flex-1 bg-transparent outline-none border-none text-white placeholder:text-slate-500 font-body text-base"
          />
          <button
            type="submit"
            disabled={running || !value.trim()}
            data-testid="command-submit"
            className="h-10 w-10 rounded-xl flex items-center justify-center transition-all disabled:opacity-40 disabled:cursor-not-allowed hover:bg-cyan-400/15"
            style={{
              background: "rgba(0, 240, 255, 0.1)",
              border: "1px solid rgba(0, 240, 255, 0.4)",
              boxShadow: running ? "none" : "0 0 18px rgba(0, 240, 255, 0.3)",
            }}
          >
            {running ? (
              <Loader2 className="h-4 w-4 text-cyan-300 animate-spin" />
            ) : (
              <Send className="h-4 w-4 text-cyan-300" />
            )}
          </button>
        </motion.form>
      </div>
    </div>
  );
}
