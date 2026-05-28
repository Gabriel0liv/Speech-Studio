import { cn } from "@/lib/utils";
import { CheckCircle2, AlertTriangle, XCircle, Loader2, Circle } from "lucide-react";
import type { JobStatus } from "@/lib/mockData";

const map: Record<JobStatus, { color: string; icon: any; label: string }> = {
  success: { color: "bg-success/15 text-success border-success/30", icon: CheckCircle2, label: "Sucesso" },
  ready: { color: "bg-success/15 text-success border-success/30", icon: CheckCircle2, label: "Pronto" },
  warning: { color: "bg-warning/15 text-warning border-warning/30", icon: AlertTriangle, label: "Aviso" },
  error: { color: "bg-destructive/15 text-destructive border-destructive/30", icon: XCircle, label: "Erro" },
  running: { color: "bg-primary/15 text-primary border-primary/30", icon: Loader2, label: "Executando" },
  missing: { color: "bg-muted/40 text-muted-foreground border-border", icon: Circle, label: "Ausente" },
};

export function StatusPill({ status, label, className }: { status: JobStatus; label?: string; className?: string }) {
  const cfg = map[status];
  const Icon = cfg.icon;
  return (
    <span className={cn("inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-xs font-medium", cfg.color, className)}>
      <Icon className={cn("size-3", status === "running" && "animate-spin")} />
      {label ?? cfg.label}
    </span>
  );
}
