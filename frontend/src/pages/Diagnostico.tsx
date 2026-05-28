import { useEffect, useMemo, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusPill } from "@/components/shared/StatusPill";
import { diagnosticLines } from "@/lib/mockData";
import { Play, Terminal } from "lucide-react";
import { toast } from "sonner";
import { getHealth, type HealthResponse } from "@/lib/api";

export default function Diagnostico() {
  const [running, setRunning] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [usingFallback, setUsingFallback] = useState(false);

  const loadHealth = async () => {
    setRunning(true);
    try {
      const response = await getHealth();
      setHealth(response);
      setUsingFallback(false);
    } catch {
      setHealth(null);
      setUsingFallback(true);
      toast.info("API offline", { description: "Mostrando diagnóstico mock do Lovable." });
    } finally {
      setRunning(false);
    }
  };

  useEffect(() => {
    void loadHealth();
  }, []);

  const renderedLines = useMemo(() => {
    if (!health) {
      return diagnosticLines;
    }

    const lines = [
      { type: "info" as const, text: "› speech-studio-api healthcheck" },
      { type: "ok" as const, text: `[OK]   Python ${health.python_version}` },
      {
        type: health.cuda.available ? "ok" as const : "warn" as const,
        text: health.cuda.available
          ? `[OK]   CUDA — ${health.cuda.gpu_name}`
          : `[WARN] CUDA — ${health.cuda.status}`,
      },
      {
        type: health.ffmpeg.available ? "ok" as const : "warn" as const,
        text: health.ffmpeg.available ? "[OK]   FFmpeg encontrado em PATH" : "[WARN] FFmpeg nao encontrado em PATH",
      },
      {
        type: health.espeak.available ? "ok" as const : "warn" as const,
        text: health.espeak.available
          ? `[OK]   eSpeak NG — ${health.espeak.path || "disponivel"}`
          : "[WARN] eSpeak NG nao encontrado",
      },
      {
        type: health.huggingface.token_configured ? "ok" as const : "warn" as const,
        text: `[${health.huggingface.token_configured ? "OK" : "WARN"}] HF_TOKEN: ${health.huggingface.token_status}`,
      },
    ];

    health.packages.forEach((pkg) => {
      const tag = pkg.status === "ok" ? "OK" : pkg.status === "warning" ? "WARN" : "ERROR";
      const type = pkg.status === "ok" ? "ok" : pkg.status === "warning" ? "warn" : "info";
      lines.push({ type, text: `[${tag}] ${pkg.label}` });
    });

    return lines;
  }, [health]);

  const renderedChecks = useMemo(() => {
    if (!health) {
      return [
        { label: "Python", value: "3.11.7", status: "success" as const },
        { label: "CUDA / GPU", value: "12.4 · RTX 4070", status: "success" as const },
        { label: "FFmpeg", value: "7.0.2", status: "success" as const },
        { label: "eSpeak NG", value: "1.52", status: "success" as const },
        { label: "Cache HF", value: "2.3 GB", status: "success" as const },
        { label: "HF Token", value: "Não encontrado", status: "warning" as const },
        { label: "Pasta outputs/", value: "Gravável", status: "success" as const },
        { label: "SQLite history.db", value: "187 registros · 4.2 MB", status: "success" as const },
      ];
    }

    return [
      { label: "Python", value: health.python_version, status: "success" as const },
      { label: "CUDA / GPU", value: health.cuda.available ? health.cuda.gpu_name : health.cuda.status, status: health.cuda.available ? "success" as const : "warning" as const },
      { label: "FFmpeg", value: health.ffmpeg.available ? "Disponivel" : "Nao encontrado", status: health.ffmpeg.available ? "success" as const : "warning" as const },
      { label: "eSpeak NG", value: health.espeak.available ? (health.espeak.path || "Disponivel") : "Nao encontrado", status: health.espeak.available ? "success" as const : "warning" as const },
      { label: "HF Token", value: health.huggingface.token_configured ? "Configurado" : "Nao encontrado", status: health.huggingface.token_configured ? "success" as const : "warning" as const },
      { label: "HF_HOME", value: health.huggingface.hf_home, status: "success" as const },
      { label: "Pasta outputs/", value: health.directories.find((item) => item.name === "Speech Directory")?.path || "Disponivel", status: "success" as const },
      { label: "Projeto", value: health.project_root, status: usingFallback ? "warning" as const : "success" as const },
    ];
  }, [health, usingFallback]);

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Diagnóstico</h1>
          <p className="text-muted-foreground mt-1">Healthcheck completo do ambiente local.</p>
        </div>
        <Button onClick={() => { void loadHealth(); }} className="bg-gradient-to-r from-primary to-accent text-primary-foreground border-0">
          <Play className="size-4" /> Executar diagnóstico
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
        <Card className="glass-panel overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-border/60 bg-secondary/40">
            <div className="flex items-center gap-2"><Terminal className="size-4 text-primary" /> <span className="text-xs font-mono">healthcheck.log</span></div>
            <div className="flex gap-1.5">
              <span className="size-2.5 rounded-full bg-destructive/60" />
              <span className="size-2.5 rounded-full bg-warning/60" />
              <span className="size-2.5 rounded-full bg-success/60" />
            </div>
          </div>
          <div className="p-5 font-mono text-xs space-y-1 bg-[hsl(224_40%_4%)] min-h-[420px]">
            {renderedLines.map((l, i) => (
              <div key={i} className={l.type === "ok" ? "text-success" : l.type === "warn" ? "text-warning" : "text-muted-foreground"}>
                {l.text}
              </div>
            ))}
            {running && <div className="text-primary animate-pulse">› executando nova verificação...</div>}
            <div className="text-primary inline-flex items-center">▍</div>
          </div>
        </Card>

        <div className="space-y-3">
          {renderedChecks.map((i) => (
            <Card key={i.label} className="glass-panel p-4 flex items-center justify-between">
              <div className="min-w-0">
                <p className="text-sm font-medium">{i.label}</p>
                <p className="text-xs font-mono text-muted-foreground truncate">{i.value}</p>
              </div>
              <StatusPill status={i.status} />
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
