import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { StatusPill } from "@/components/shared/StatusPill";
import { transcriptPreview, speakerProfiles } from "@/lib/mockData";
import { UploadCloud, Play, FileText, Copy, FileAudio } from "lucide-react";
import { toast } from "sonner";

const formats = ["mp3", "wav", "mp4", "mkv", "mov", "m4a", "webm"];

export default function Transcricao() {
  const [diarization, setDiarization] = useState(true);
  const [outputs, setOutputs] = useState({ txt: true, json: true, srt: true, vtt: false });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Transcrição</h1>
        <p className="text-muted-foreground mt-1">WhisperX + diarização local de speakers.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
        <div className="space-y-6">
          <Card className="glass-panel p-8 border-dashed border-2 hover:border-primary/60 transition group">
            <div className="flex flex-col items-center text-center py-6">
              <div className="size-16 rounded-2xl bg-primary/10 border border-primary/30 flex items-center justify-center mb-4 group-hover:scale-110 transition">
                <UploadCloud className="size-7 text-primary" />
              </div>
              <h3 className="font-semibold text-lg">Arraste seu arquivo aqui</h3>
              <p className="text-sm text-muted-foreground mt-1">ou clique para selecionar áudio ou vídeo</p>
              <Button className="mt-5" variant="outline" onClick={() => toast.info("Selecione um arquivo (demo)")}>
                Selecionar arquivo
              </Button>
              <div className="flex flex-wrap gap-1.5 justify-center mt-6">
                {formats.map((f) => <Badge key={f} variant="secondary" className="font-mono text-[10px] uppercase">{f}</Badge>)}
              </div>
            </div>
          </Card>

          <Card className="glass-panel p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <FileAudio className="size-4 text-primary" />
                <span className="font-medium text-sm">podcast_ep32.mp3</span>
              </div>
              <StatusPill status="ready" label="Pronto" />
            </div>
            <div className="grid grid-cols-3 gap-3 text-xs">
              <Info label="Duração" value="47:12" />
              <Info label="Tamanho" value="68.4 MB" />
              <Info label="Sample rate" value="44.1 kHz" />
            </div>
          </Card>

          <Card className="glass-panel p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold flex items-center gap-2"><FileText className="size-4 text-primary" /> Pré-visualização</h3>
              <Badge variant="outline" className="text-xs">5 segmentos · 3 falantes</Badge>
            </div>
            <div className="space-y-2 max-h-80 overflow-auto pr-2">
              {transcriptPreview.map((seg, i) => (
                <div key={i} className="flex gap-3 p-3 rounded-lg bg-secondary/40 border border-border/40">
                  <span className="font-mono text-[11px] text-muted-foreground shrink-0 mt-0.5">{seg.time}</span>
                  <div className="min-w-0">
                    <Badge className="text-[10px] mb-1 bg-accent/15 text-accent border-accent/30">{seg.speaker}</Badge>
                    <p className="text-sm leading-relaxed">{seg.text}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 pt-4 border-t border-border/60 space-y-2">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Arquivos gerados</p>
              {["transcript.txt", "transcript.json", "transcript.srt"].map((f) => (
                <div key={f} className="flex items-center justify-between p-2 rounded bg-background/40 border border-border/40">
                  <span className="font-mono text-xs">outputs/transcriptions/{f}</span>
                  <Button size="sm" variant="ghost" className="h-7" onClick={() => toast.success("Caminho copiado")}>
                    <Copy className="size-3" />
                  </Button>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <Card className="glass-panel p-6 h-fit lg:sticky lg:top-24 space-y-5">
          <h3 className="font-semibold">Configurações</h3>
          <Setting label="Modelo Whisper">
            <Select defaultValue="large"><SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>{["tiny","base","small","medium","large"].map(v=><SelectItem key={v} value={v}>{v}</SelectItem>)}</SelectContent>
            </Select>
          </Setting>
          <div className="grid grid-cols-2 gap-3">
            <Setting label="Idioma">
              <Select defaultValue="auto"><SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{["auto","pt","en","es"].map(v=><SelectItem key={v} value={v}>{v}</SelectItem>)}</SelectContent>
              </Select>
            </Setting>
            <Setting label="Device">
              <Select defaultValue="cuda"><SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{["auto","cuda","cpu"].map(v=><SelectItem key={v} value={v}>{v}</SelectItem>)}</SelectContent>
              </Select>
            </Setting>
            <Setting label="Compute type">
              <Select defaultValue="float16"><SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{["int8","float16","float32"].map(v=><SelectItem key={v} value={v}>{v}</SelectItem>)}</SelectContent>
              </Select>
            </Setting>
            <Setting label="Batch size"><Input type="number" defaultValue={16} /></Setting>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/40 border border-border/40">
            <div>
              <p className="text-sm font-medium">Diarização de speakers</p>
              <p className="text-xs text-muted-foreground">Identifica quem fala (pyannote)</p>
            </div>
            <Switch checked={diarization} onCheckedChange={setDiarization} />
          </div>

          {diarization && (
            <div className="grid grid-cols-3 gap-2 pl-3 border-l-2 border-primary/40">
              <Setting label="Num"><Input type="number" placeholder="auto" /></Setting>
              <Setting label="Min"><Input type="number" defaultValue={2} /></Setting>
              <Setting label="Max"><Input type="number" defaultValue={4} /></Setting>
            </div>
          )}

          <Setting label="Perfil de speakers">
            <Select defaultValue="podcast"><SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>{speakerProfiles.map(p=><SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}</SelectContent>
            </Select>
          </Setting>

          <div>
            <Label className="text-xs uppercase tracking-wider text-muted-foreground">Formatos de saída</Label>
            <div className="flex flex-wrap gap-3 mt-2">
              {Object.entries(outputs).map(([k, v]) => (
                <label key={k} className="flex items-center gap-2 cursor-pointer text-sm">
                  <Checkbox checked={v} onCheckedChange={(c) => setOutputs({ ...outputs, [k]: !!c })} />
                  <span className="font-mono uppercase">{k}</span>
                </label>
              ))}
            </div>
          </div>

          <Button className="w-full bg-gradient-to-r from-primary to-accent text-primary-foreground hover:opacity-90 border-0" onClick={() => toast.success("Transcrição iniciada", { description: "Estimativa: ~4 min" })}>
            <Play className="size-4 mr-1" /> Iniciar transcrição
          </Button>
        </Card>
      </div>
    </div>
  );
}

function Setting({ label, children }: any) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs uppercase tracking-wider text-muted-foreground">{label}</Label>
      {children}
    </div>
  );
}
function Info({ label, value }: any) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className="font-mono text-sm mt-0.5">{value}</p>
    </div>
  );
}
