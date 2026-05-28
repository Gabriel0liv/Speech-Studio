import { mockStats, recentJobs, healthChecks } from "@/lib/mockData";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatusPill } from "@/components/shared/StatusPill";
import { FileAudio, Mic, Package, ListChecks, HardDrive, ArrowRight, Activity } from "lucide-react";
import { Link } from "react-router-dom";

const statCards = [
  { label: "Transcrições hoje", value: mockStats.transcriptionsToday, icon: FileAudio, accent: "from-cyan-500/20 to-cyan-500/0" },
  { label: "Áudios gerados", value: mockStats.audiosGenerated, icon: Mic, accent: "from-purple-500/20 to-purple-500/0" },
  { label: "Modelos disponíveis", value: mockStats.modelsAvailable, icon: Package, accent: "from-emerald-500/20 to-emerald-500/0" },
  { label: "Jobs recentes", value: mockStats.recentJobs, icon: ListChecks, accent: "from-amber-500/20 to-amber-500/0" },
  { label: "Storage local", value: mockStats.storage, icon: HardDrive, accent: "from-rose-500/20 to-rose-500/0" },
];

export default function Dashboard() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Painel</h1>
        <p className="text-muted-foreground mt-1">Visão geral do seu estúdio de voz local.</p>
      </div>

      <div className="grid gap-4 grid-cols-2 lg:grid-cols-5">
        {statCards.map((s) => (
          <Card key={s.label} className="relative overflow-hidden p-5 glass-panel group hover:border-primary/40 transition-all">
            <div className={`absolute inset-0 bg-gradient-to-br ${s.accent} opacity-60 pointer-events-none`} />
            <div className="relative flex items-start justify-between">
              <div>
                <p className="text-xs uppercase tracking-wider text-muted-foreground font-medium">{s.label}</p>
                <p className="text-2xl font-bold mt-2">{s.value}</p>
              </div>
              <div className="p-2 rounded-lg bg-background/60 border border-border/60">
                <s.icon className="size-4 text-primary" />
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-4">Pipeline rápido</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <Link to="/transcricao">
            <Card className="p-6 glass-panel hover:border-primary/60 hover:shadow-[0_0_40px_-10px_hsl(var(--primary)/0.4)] transition-all group cursor-pointer h-full">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-xl bg-primary/10 border border-primary/30">
                  <FileAudio className="size-6 text-primary" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">Transcrever áudio/vídeo</h3>
                  <p className="text-sm text-muted-foreground mt-1">WhisperX + diarização pyannote, totalmente local.</p>
                </div>
                <ArrowRight className="size-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
              </div>
            </Card>
          </Link>
          <Link to="/tts">
            <Card className="p-6 glass-panel hover:border-accent/60 hover:shadow-[0_0_40px_-10px_hsl(var(--accent)/0.4)] transition-all group cursor-pointer h-full">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-xl bg-accent/10 border border-accent/30">
                  <Mic className="size-6 text-accent" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">Gerar voz a partir de texto</h3>
                  <p className="text-sm text-muted-foreground mt-1">Kokoro e Piper com vozes PT-BR de alta qualidade.</p>
                </div>
                <ArrowRight className="size-5 text-muted-foreground group-hover:text-accent group-hover:translate-x-1 transition-all" />
              </div>
            </Card>
          </Link>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="glass-panel p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">Jobs recentes</h2>
            <Button variant="ghost" size="sm" asChild>
              <Link to="/historico">Ver tudo <ArrowRight className="ml-1 size-3" /></Link>
            </Button>
          </div>
          <div className="space-y-2">
            {recentJobs.slice(0, 6).map((j) => (
              <div key={j.id} className="flex items-center justify-between p-3 rounded-lg bg-secondary/40 border border-border/40 hover:border-border transition">
                <div className="flex items-center gap-3 min-w-0">
                  <Badge variant="outline" className="font-mono text-[10px]">{j.type}</Badge>
                  <span className="truncate text-sm">{j.name}</span>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-xs text-muted-foreground hidden sm:block">{j.time}</span>
                  <StatusPill status={j.status} />
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card className="glass-panel p-6">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="size-4 text-success" />
            <h2 className="font-semibold">Saúde do sistema</h2>
          </div>
          <div className="space-y-2.5">
            {healthChecks.map((h) => (
              <div key={h.name} className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">{h.name}</span>
                <StatusPill status={h.status} label={h.label} />
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
