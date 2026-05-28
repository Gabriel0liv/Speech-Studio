import { useEffect, useMemo, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { StatusPill } from "@/components/shared/StatusPill";
import { Waveform } from "@/components/shared/Waveform";
import { recentJobs } from "@/lib/mockData";
import { Search, Play, Copy, FolderOpen, RotateCcw, Trash2, FileAudio } from "lucide-react";
import { toast } from "sonner";
import { getHistory, type HistoryJob } from "@/lib/api";

const filters = ["Todos", "Transcrição", "TTS", "Sucesso", "Falha", "Hoje", "Esta semana"];
const allJobs = [
  ...recentJobs,
  { id: "7", type: "TTS", name: "anuncio_kokoro_santa.mp3", status: "success" as const, time: "ontem" },
  { id: "8", type: "STT", name: "aula_completa.mp4", status: "success" as const, time: "2 dias" },
  { id: "9", type: "TTS", name: "tutorial_piper.wav", status: "warning" as const, time: "2 dias" },
];

export default function Historico() {
  const [active, setActive] = useState("Todos");
  const [jobs, setJobs] = useState<HistoryJob[]>(allJobs);
  const [selected, setSelected] = useState<HistoryJob>(allJobs[1]);
  const [query, setQuery] = useState("");

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const response = await getHistory();
        if (response.length > 0) {
          setJobs(response);
          setSelected(response[0]);
        }
      } catch {
        toast.info("API offline", { description: "Mostrando histórico mock do Lovable." });
      }
    };

    void loadHistory();
  }, []);

  const filteredJobs = useMemo(() => {
    return jobs.filter((job) => {
      const type = (job.job_type || job.type || "").toUpperCase();
      const status = (job.status || "").toLowerCase();
      const name = job.input_name || job.name || "";
      const matchesQuery = !query || `${name} ${type} ${status}`.toLowerCase().includes(query.toLowerCase());

      if (!matchesQuery) return false;
      if (active === "Todos") return true;
      if (active === "TTS") return type === "TTS";
      if (active === "Transcrição") return type === "STT";
      if (active === "Sucesso") return status === "success";
      if (active === "Falha") return status === "failed" || status === "error";
      return true;
    });
  }, [active, jobs, query]);

  useEffect(() => {
    if (!filteredJobs.find((job) => job.id === selected?.id) && filteredJobs[0]) {
      setSelected(filteredJobs[0]);
    }
  }, [filteredJobs, selected]);

  const selectedType = (selected?.job_type || selected?.type || "").toUpperCase();
  const selectedName = selected?.input_name || selected?.name || "Sem nome";
  const outputPath = selected?.primary_output_path || selected?.output_dir || "N/D";
  const relativeTime = selected?.time || selected?.created_at || "agora";

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Histórico</h1>
          <p className="text-muted-foreground mt-1">Todos os jobs locais (SQLite).</p>
        </div>
        <Button variant="outline" onClick={() => toast.warning("Histórico limpo", { description: "Arquivos de saída foram preservados." })}>
          <Trash2 className="size-4" /> Limpar histórico
        </Button>
      </div>

      <Card className="glass-panel p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input placeholder="Buscar por nome, modelo, voz..." className="pl-9 bg-background/60" value={query} onChange={(e) => setQuery(e.target.value)} />
          </div>
          <div className="flex flex-wrap gap-1.5">
            {filters.map((f) => (
              <Button key={f} variant={active === f ? "default" : "outline"} size="sm" onClick={() => setActive(f)} className={active===f ? "bg-primary text-primary-foreground" : ""}>
                {f}
              </Button>
            ))}
          </div>
        </div>
      </Card>

      <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <Card className="glass-panel overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-secondary/40 text-xs uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="text-left p-3">Tipo</th>
                <th className="text-left p-3">Arquivo</th>
                <th className="text-left p-3">Quando</th>
                <th className="text-left p-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredJobs.map((j) => (
                <tr key={j.id} onClick={() => setSelected(j)} className={`border-t border-border/40 cursor-pointer hover:bg-secondary/30 transition ${selected?.id===j.id ? "bg-primary/5" : ""}`}>
                  <td className="p-3"><Badge variant="outline" className="font-mono text-[10px]">{(j.job_type || j.type || "JOB").toUpperCase()}</Badge></td>
                  <td className="p-3 font-medium truncate max-w-[260px]">{j.input_name || j.name || "Sem nome"}</td>
                  <td className="p-3 text-muted-foreground">{j.time || j.created_at || "-"}</td>
                  <td className="p-3"><StatusPill status={(j.status as any) || "warning"} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <Card className="glass-panel p-6 h-fit lg:sticky lg:top-24 space-y-4">
          <div className="flex items-center gap-2">
            <FileAudio className="size-4 text-primary" />
            <h3 className="font-semibold truncate">{selectedName}</h3>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="font-mono text-[10px]">{selectedType || "JOB"}</Badge>
            <StatusPill status={(selected?.status as any) || "warning"} />
          </div>

          {selectedType === "TTS" ? (
            <>
              <div className="p-4 rounded-lg bg-background/40 border border-border/40">
                <Waveform />
                <div className="flex items-center justify-between mt-3">
                  <Button size="sm" variant="outline" onClick={() => selected?.file_url ? window.open(selected.file_url, "_blank") : toast.info("Nenhum arquivo reproduzível disponível")}><Play className="size-3" /> Reproduzir</Button>
                  <span className="text-xs font-mono text-muted-foreground">{relativeTime}</span>
                </div>
              </div>
              <Detail label="Engine" value={selected?.engine || "N/D"} />
              <Detail label="Voz" value={selected?.voice || "N/D"} />
              <Detail label="Formato" value={(selected?.output_format || "N/D").toUpperCase()} />
              <Detail label="Texto" value={selected?.text_snippet ? `"${selected.text_snippet}"` : `"Sem prévia disponível"`} />
              <Detail label="Saída" value={outputPath} mono />
            </>
          ) : (
            <>
              <Detail label="Modelo" value={selected?.model || "N/D"} />
              <Detail label="Idioma" value={selected?.language || "auto"} />
              <Detail label="Diarização" value={selected?.metadata_json || "Ver logs/JSON"} />
              <Detail label="Trecho" value={selected?.text_snippet ? `"${selected.text_snippet}"` : `"Sem prévia disponível"`} />
              <Detail label="Arquivos" value={selected?.primary_output_path ? "Artefato principal disponível" : "Ver diretório de saída"} />
              <Detail label="Saída" value={outputPath} mono />
            </>
          )}

          <div className="flex flex-wrap gap-2 pt-2 border-t border-border/60">
            <Button size="sm" variant="outline" onClick={() => toast.success("Job reutilizado")}><RotateCcw className="size-3" /> Reutilizar</Button>
            <Button size="sm" variant="outline" onClick={() => { navigator.clipboard.writeText(outputPath); toast.success("Caminho copiado"); }}><Copy className="size-3" /> Copiar</Button>
            <Button size="sm" variant="outline" onClick={() => selected?.file_url ? window.open(selected.file_url, "_blank") : toast.info("Nenhum arquivo disponível")}><FolderOpen className="size-3" /> Abrir saída</Button>
          </div>
        </Card>
      </div>
    </div>
  );
}

function Detail({ label, value, mono }: any) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className={`text-sm mt-0.5 ${mono ? "font-mono text-xs break-all" : ""}`}>{value}</p>
    </div>
  );
}
