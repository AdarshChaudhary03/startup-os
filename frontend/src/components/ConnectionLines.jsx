import { useEffect, useState, useCallback } from "react";

export default function ConnectionLines({ activeAgentId, canvasRef }) {
  const [path, setPath] = useState(null);
  const [size, setSize] = useState({ w: 0, h: 0 });

  const compute = useCallback(() => {
    if (!canvasRef.current) return;
    const canvasEl = canvasRef.current;
    const canvasRect = canvasEl.getBoundingClientRect();
    setSize({ w: canvasRect.width, h: canvasRect.height });

    if (!activeAgentId) {
      setPath(null);
      return;
    }

    const ceoEl = canvasEl.querySelector('[data-testid="ceo-node"]');
    const agentEl = canvasEl.querySelector(`[data-testid="agent-card-${activeAgentId}"]`);
    if (!ceoEl || !agentEl) {
      setPath(null);
      return;
    }

    const ceoRect = ceoEl.getBoundingClientRect();
    const cx = ceoRect.left - canvasRect.left + ceoRect.width / 2;
    const cy = ceoRect.top - canvasRect.top + ceoRect.height;

    const r = agentEl.getBoundingClientRect();
    const ax = r.left - canvasRect.left + r.width / 2;
    const ay = r.top - canvasRect.top;
    const midY = (cy + ay) / 2;
    const d = `M ${cx},${cy} C ${cx},${midY} ${ax},${midY} ${ax},${ay}`;
    setPath({ id: activeAgentId, d });
  }, [activeAgentId, canvasRef]);

  useEffect(() => {
    const timeouts = [50, 200, 500, 1000].map((t) => setTimeout(compute, t));
    const handle = () => compute();
    window.addEventListener("resize", handle);
    window.addEventListener("scroll", handle, true);
    const interval = setInterval(handle, 1000);
    return () => {
      timeouts.forEach(clearTimeout);
      window.removeEventListener("resize", handle);
      window.removeEventListener("scroll", handle, true);
      clearInterval(interval);
    };
  }, [compute]);

  return (
    <svg
      className="absolute inset-0 pointer-events-none"
      width={size.w}
      height={size.h}
      style={{ left: 0, top: 0 }}
      data-testid="connection-lines"
    >
      <defs>
        <linearGradient id="lineActive" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#FF00FF" stopOpacity="1" />
          <stop offset="100%" stopColor="#00F0FF" stopOpacity="1" />
        </linearGradient>
      </defs>

      {path && (
        <g key={path.id}>
          <path d={path.d} fill="none" stroke="url(#lineActive)" strokeWidth={2} opacity={0.85} />
          <path d={path.d} fill="none" stroke="#00F0FF" strokeWidth={2.6} className="path-flow" strokeLinecap="round" />
        </g>
      )}
    </svg>
  );
}
