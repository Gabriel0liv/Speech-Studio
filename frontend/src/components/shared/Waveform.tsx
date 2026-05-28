import { useMemo } from "react";

export function Waveform({ bars = 64, active = false, className = "" }: { bars?: number; active?: boolean; className?: string }) {
  const heights = useMemo(
    () => Array.from({ length: bars }, (_, i) => 20 + Math.sin(i * 0.5) * 30 + Math.random() * 50),
    [bars]
  );
  return (
    <div className={`flex items-center gap-[2px] h-12 ${className}`}>
      {heights.map((h, i) => (
        <div
          key={i}
          className={`flex-1 rounded-full bg-gradient-to-t from-primary/40 to-accent/80 ${active ? "animate-pulse" : ""}`}
          style={{ height: `${Math.min(h, 100)}%`, animationDelay: `${i * 30}ms` }}
        />
      ))}
    </div>
  );
}
