import { SidebarTrigger } from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatusPill } from "@/components/shared/StatusPill";
import { FolderOpen, Stethoscope, Cpu, FileVideo, AudioLines, Key } from "lucide-react";
import { toast } from "sonner";

export function TopBar() {
  return (
    <header className="sticky top-0 z-30 h-16 border-b border-border/60 bg-background/80 backdrop-blur-xl flex items-center gap-3 px-4 lg:px-6">
      <SidebarTrigger className="shrink-0" />
      <div className="flex items-center gap-3 min-w-0">
        <h1 className="text-base font-semibold hidden sm:block">Speech Studio Local</h1>
        <Badge className="bg-gradient-to-r from-primary/20 to-accent/20 text-primary border-primary/30 font-medium">
          Local-first
        </Badge>
      </div>

      <div className="hidden lg:flex items-center gap-1.5 mx-4">
        <Pill icon={Cpu} label="GPU" status="success" />
        <Pill icon={FileVideo} label="FFmpeg" status="success" />
        <Pill icon={AudioLines} label="eSpeak" status="success" />
        <Pill icon={Key} label="HF Token" status="warning" valLabel="Ausente" />
      </div>

      <div className="ml-auto flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={() => toast.success("Pasta de saídas aberta", { description: "outputs/" })}>
          <FolderOpen className="size-4" />
          <span className="hidden md:inline">Saídas</span>
        </Button>
        <Button size="sm" className="bg-gradient-to-r from-primary to-accent text-primary-foreground hover:opacity-90 border-0" onClick={() => toast.success("Healthcheck iniciado", { description: "Verificando ambiente local..." })}>
          <Stethoscope className="size-4" />
          <span className="hidden md:inline">Healthcheck</span>
        </Button>
      </div>
    </header>
  );
}

function Pill({ icon: Icon, label, status, valLabel }: any) {
  const cls = status === "success" ? "text-success border-success/30 bg-success/10" : "text-warning border-warning/30 bg-warning/10";
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full border text-[11px] font-medium ${cls}`}>
      <Icon className="size-3" /> {label} {valLabel ? `· ${valLabel}` : "· OK"}
    </span>
  );
}
