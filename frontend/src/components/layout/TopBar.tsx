import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { FolderOpen, Stethoscope, Cpu, FileVideo, AudioLines, Key, WifiOff } from "lucide-react";
import { toast } from "sonner";
import { getHealth, type HealthResponse } from "@/lib/api";

type PillStatus = "success" | "warning";

export function TopBar() {
  const navigate = useNavigate();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [offline, setOffline] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const loadHealth = async (showToast = false) => {
    setRefreshing(true);
    try {
      const response = await getHealth();
      setHealth(response);
      setOffline(false);
      if (showToast) {
        toast.success("Status atualizado");
      }
    } catch {
      setHealth(null);
      setOffline(true);
      if (showToast) {
        toast.info("API offline", { description: "Status local indisponível no momento." });
      }
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    void loadHealth();
  }, []);

  const pills = useMemo(() => {
    if (offline || !health) {
      return [
        { icon: WifiOff, label: "API", status: "warning" as const, value: "offline" },
        { icon: Cpu, label: "GPU", status: "warning" as const, value: "indisp." },
        { icon: FileVideo, label: "FFmpeg", status: "warning" as const, value: "indisp." },
        { icon: AudioLines, label: "eSpeak", status: "warning" as const, value: "indisp." },
        { icon: Key, label: "HF Token", status: "warning" as const, value: "indisp." },
      ];
    }

    return [
      {
        icon: Cpu,
        label: "GPU",
        status: health.cuda.available ? "success" as const : "warning" as const,
        value: health.cuda.available ? "OK" : "CPU",
      },
      {
        icon: FileVideo,
        label: "FFmpeg",
        status: health.ffmpeg.available ? "success" as const : "warning" as const,
        value: health.ffmpeg.available ? "OK" : "Ausente",
      },
      {
        icon: AudioLines,
        label: "eSpeak",
        status: health.espeak.available ? "success" as const : "warning" as const,
        value: health.espeak.available ? "OK" : "Ausente",
      },
      {
        icon: Key,
        label: "HF Token",
        status: health.huggingface.token_configured ? "success" as const : "warning" as const,
        value: health.huggingface.token_configured ? "OK" : "Ausente",
      },
    ];
  }, [health, offline]);

  return (
    <header className="sticky top-0 z-30 h-16 border-b border-border/60 bg-background/80 backdrop-blur-xl flex items-center gap-3 px-4 lg:px-6">
      <SidebarTrigger className="shrink-0" />
      <div className="flex items-center gap-3 min-w-0">
        <h1 className="text-base font-semibold hidden sm:block">Speech Studio Local</h1>
        <Badge className="bg-gradient-to-r from-primary/20 to-accent/20 text-primary border-primary/30 font-medium">
          Local-first
        </Badge>
        {offline ? <Badge variant="outline" className="text-warning border-warning/30">API offline</Badge> : null}
      </div>

      <div className="hidden lg:flex items-center gap-1.5 mx-4">
        {pills.map((pill) => (
          <Pill key={pill.label} icon={pill.icon} label={pill.label} status={pill.status} valLabel={pill.value} />
        ))}
      </div>

      <div className="ml-auto flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={() => toast.info("Abrir pasta ainda não implementado")}>
          <FolderOpen className="size-4" />
          <span className="hidden md:inline">Saídas</span>
        </Button>
        <Button
          size="sm"
          className="bg-gradient-to-r from-primary to-accent text-primary-foreground hover:opacity-90 border-0"
          onClick={() => {
            void loadHealth(true);
            navigate("/diagnostico");
          }}
        >
          <Stethoscope className={`size-4 ${refreshing ? "animate-pulse" : ""}`} />
          <span className="hidden md:inline">Healthcheck</span>
        </Button>
      </div>
    </header>
  );
}

function Pill({
  icon: Icon,
  label,
  status,
  valLabel,
}: {
  icon: typeof Cpu;
  label: string;
  status: PillStatus;
  valLabel: string;
}) {
  const cls = status === "success" ? "text-success border-success/30 bg-success/10" : "text-warning border-warning/30 bg-warning/10";
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full border text-[11px] font-medium ${cls}`}>
      <Icon className="size-3" /> {label} · {valLabel}
    </span>
  );
}
