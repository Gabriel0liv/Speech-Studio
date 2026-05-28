import { useMemo, useRef, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { StatusPill } from "@/components/shared/StatusPill";
import { Waveform } from "@/components/shared/Waveform";
import { voices } from "@/lib/mockData";
import { Play, Pause, Sparkles, Wand2, BarChart3, FileJson, FileText, Mic2, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { analyzePtbrText, compareVoices, generateTtsFull, generateTtsPreview } from "@/lib/api";

const sampleText = "Ola pessoal, hoje eu vou falar sobre inteligencia artificial local e como voce pode usar voces sinteticas em portugues brasileiro sem depender de APIs pagas. E muito mais simples do que parece, e nao precisa de conexao com a internet.";

export default function TextoParaVoz() {
  const [text, setText] = useState(sampleText);
  const [engine, setEngine] = useState("kokoro");
  const [voice, setVoice] = useState("dora");
  const [speed, setSpeed] = useState([1]);
  const [previewChars, setPreviewChars] = useState([200]);
  const [analyze, setAnalyze] = useState(true);
  const [playing, setPlaying] = useState(false);
  const [issues, setIssues] = useState([
    "O texto tem poucas palavras acentuadas (apenas 1 de 42).",
    "Sugestão: Ola → Olá, voce → você, nao → não, E → É.",
    "3 abreviações detectadas que podem afetar a pronúncia.",
  ]);
  const [previewAudioUrl, setPreviewAudioUrl] = useState<string | null>(null);
  const [previewLogs, setPreviewLogs] = useState<string>("");
  const [compareReportJsonUrl, setCompareReportJsonUrl] = useState<string | null>(null);
  const [compareReportMdUrl, setCompareReportMdUrl] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const filteredVoices = voices.filter((v) => v.engine.toLowerCase() === engine);
  const selectedVoice = useMemo(() => filteredVoices.find((item) => item.id === voice), [filteredVoices, voice]);

  const buildPayload = () => ({
    text,
    engine,
    voice,
    format: "wav",
    preview_chars: previewChars[0],
    speed: speed[0],
    normalize_ptbr: true,
    analyze_ptbr: analyze,
    preset: null,
  });

  const handleAnalyze = async () => {
    try {
      const response = await analyzePtbrText(text);
      const nextIssues = [
        ...response.analysis.warnings,
        ...response.analysis.suggestions.map((item: { note: string }) => item.note),
      ];
      setIssues(nextIssues.length > 0 ? nextIssues : ["Nenhum ajuste PT-BR recomendado."]);
      toast.success("Texto analisado");
    } catch (error) {
      toast.info("API offline", { description: "Mantendo sugestões mock do Lovable." });
    }
  };

  const handlePreview = async () => {
    try {
      const response = await generateTtsPreview(buildPayload());
      if (response.audio_url) {
        setPreviewAudioUrl(response.audio_url);
        setPreviewLogs(response.logs || "");
      }
      if (response.analysis) {
        const nextIssues = [
          ...response.analysis.warnings,
          ...response.analysis.suggestions.map((item: { note: string }) => item.note),
        ];
        setIssues(nextIssues.length > 0 ? nextIssues : issues);
      }
      toast.success("Preview gerado", { description: response.audio_path || "Áudio disponível via API." });
    } catch (error: any) {
      toast.error("Falha ao gerar preview", { description: error?.message || "API indisponível." });
    }
  };

  const handleGenerate = async () => {
    try {
      const response = await generateTtsFull(buildPayload());
      toast.success("Áudio completo gerado", { description: response.audio_path || "Arquivo pronto em outputs/speech/." });
    } catch (error: any) {
      toast.error("Falha ao gerar áudio", { description: error?.message || "API indisponível." });
    }
  };

  const handleCompare = async () => {
    try {
      const response = await compareVoices({ text, language: "pt-br", normalize_ptbr: true });
      setCompareReportJsonUrl(response.report_json_url || null);
      setCompareReportMdUrl(response.report_md_url || null);
      toast.success("Comparativo PT-BR gerado", { description: response.output_dir || "Veja os relatórios da API." });
    } catch (error: any) {
      toast.error("Falha ao comparar vozes", { description: error?.message || "API indisponível." });
    }
  };

  const togglePlayback = async () => {
    if (!audioRef.current || !previewAudioUrl) {
      toast.info("Gere um preview primeiro");
      return;
    }
    if (playing) {
      audioRef.current.pause();
      setPlaying(false);
      return;
    }
    await audioRef.current.play();
    setPlaying(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Texto para Voz</h1>
          <p className="text-muted-foreground mt-1">Síntese local com Kokoro e Piper.</p>
        </div>
        <Button variant="outline" onClick={() => { void handleCompare(); }}>
          <BarChart3 className="size-4" /> Comparar vozes PT-BR
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <div className="space-y-6">
          <Card className="glass-panel p-6">
            <div className="flex items-center justify-between mb-3">
              <Label className="text-xs uppercase tracking-wider text-muted-foreground">Texto do script</Label>
              <span className="text-xs font-mono text-muted-foreground">{text.length} caracteres · ~{Math.ceil(text.length/15)}s</span>
            </div>
            <Textarea value={text} onChange={(e) => setText(e.target.value)} rows={10} className="resize-none font-sans text-base leading-relaxed bg-background/60" placeholder="Digite ou cole seu texto..." />
            <div className="flex flex-wrap gap-2 mt-4">
              <Button variant="outline" size="sm" onClick={() => { void handleAnalyze(); }}><Wand2 className="size-4" /> Analisar texto</Button>
              <Button variant="outline" size="sm" onClick={() => { void handlePreview(); }}><Sparkles className="size-4" /> Gerar preview</Button>
              <Button size="sm" className="bg-gradient-to-r from-primary to-accent text-primary-foreground border-0 hover:opacity-90 ml-auto" onClick={() => { void handleGenerate(); }}>
                <Mic2 className="size-4" /> Gerar áudio completo
              </Button>
            </div>
          </Card>

          {analyze && (
            <Card className="glass-panel p-5 border-warning/30">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="size-4 text-warning" />
                <h3 className="font-semibold">Análise PT-BR</h3>
                <Badge variant="outline" className="ml-auto text-xs">{issues.length} sugestões</Badge>
              </div>
              <ul className="space-y-2">
                {issues.map((i) => (
                  <li key={i} className="flex gap-2 text-sm">
                    <span className="text-warning mt-0.5">›</span>
                    <span className="text-muted-foreground">{i}</span>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          <Card className="glass-panel p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">Preview de áudio</h3>
              <Badge variant="outline" className="text-xs">{engine.charAt(0).toUpperCase() + engine.slice(1)} · {selectedVoice?.name || voice} · {speed[0].toFixed(1)}x</Badge>
            </div>
            <div className="flex items-center gap-4">
              <Button size="icon" onClick={() => { void togglePlayback(); }} className="size-12 rounded-full bg-gradient-to-br from-primary to-accent text-primary-foreground border-0 shadow-[0_0_30px_hsl(var(--primary)/0.4)]">
                {playing ? <Pause className="size-5" /> : <Play className="size-5 ml-0.5" />}
              </Button>
              <div className="flex-1">
                <Waveform active={playing} />
                <div className="flex justify-between text-[11px] font-mono text-muted-foreground mt-1">
                  <span>00:00</span><span>00:14</span>
                </div>
              </div>
            </div>
            <audio ref={audioRef} src={previewAudioUrl || undefined} hidden onEnded={() => setPlaying(false)} onPause={() => setPlaying(false)} />
            {previewLogs ? <p className="text-[11px] text-muted-foreground mt-3 line-clamp-2">{previewLogs}</p> : null}
          </Card>

          <div>
            <h3 className="font-semibold mb-3">Comparação de vozes PT-BR</h3>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {voices.map((v) => (
                <Card key={v.id} className="glass-panel p-4 hover:border-primary/40 transition">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="font-semibold">{v.name}</p>
                      <p className="text-[11px] text-muted-foreground">{v.engine} · {v.lang}</p>
                    </div>
                    <StatusPill status={v.status} />
                  </div>
                  <p className="text-xs text-muted-foreground mb-3">{v.style}</p>
                  <Waveform bars={32} className="h-8" />
                  <Button variant="ghost" size="sm" className="w-full mt-2 h-8"><Play className="size-3" /> Tocar amostra</Button>
                </Card>
              ))}
            </div>
            <div className="flex gap-3 mt-4">
              <Button variant="outline" size="sm" onClick={() => compareReportJsonUrl ? window.open(compareReportJsonUrl, "_blank") : toast.info("Gere um comparativo primeiro")}><FileJson className="size-4" /> compare_report.json</Button>
              <Button variant="outline" size="sm" onClick={() => compareReportMdUrl ? window.open(compareReportMdUrl, "_blank") : toast.info("Gere um comparativo primeiro")}><FileText className="size-4" /> compare_report.md</Button>
            </div>
          </div>
        </div>

        <Card className="glass-panel p-6 h-fit lg:sticky lg:top-24 space-y-5">
          <h3 className="font-semibold">Controles de geração</h3>

          <div className="grid grid-cols-2 gap-3">
            <Setting label="Engine">
              <Select value={engine} onValueChange={setEngine}><SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem value="kokoro">Kokoro</SelectItem><SelectItem value="piper">Piper</SelectItem></SelectContent>
              </Select>
            </Setting>
            <Setting label="Formato">
              <Select defaultValue="wav"><SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem value="wav">WAV</SelectItem><SelectItem value="mp3">MP3</SelectItem></SelectContent>
              </Select>
            </Setting>
          </div>

          <Setting label="Voz">
            <Select value={voice} onValueChange={setVoice}><SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>{filteredVoices.map((v) => <SelectItem key={v.id} value={v.id}>{v.name} — {v.style}</SelectItem>)}</SelectContent>
            </Select>
          </Setting>

          <div className="grid grid-cols-3 gap-2">
            {filteredVoices.map((v) => (
              <button key={v.id} onClick={() => setVoice(v.id)} className={`p-3 rounded-lg border text-left transition ${voice===v.id ? "border-primary bg-primary/10" : "border-border hover:border-border/80 bg-secondary/40"}`}>
                <p className="font-medium text-sm">{v.name}</p>
                <p className="text-[10px] text-muted-foreground truncate">{v.lang}</p>
              </button>
            ))}
          </div>

          <Setting label={`Velocidade · ${speed[0].toFixed(2)}x`}>
            <Slider value={speed} onValueChange={setSpeed} min={0.5} max={2} step={0.05} />
          </Setting>
          <Setting label={`Caracteres de preview · ${previewChars[0]}`}>
            <Slider value={previewChars} onValueChange={setPreviewChars} min={50} max={500} step={10} />
          </Setting>

          <div className="space-y-2.5 pt-2 border-t border-border/60">
            <Toggle label="Analisar texto PT-BR" desc="Sugere acentuação e correções" checked={analyze} onChange={setAnalyze} />
            <Toggle label="Normalização PT-BR" desc="Expande abreviações e números" checked />
          </div>
        </Card>
      </div>
    </div>
  );
}

function Setting({ label, children }: any) {
  return (<div className="space-y-1.5"><Label className="text-xs uppercase tracking-wider text-muted-foreground">{label}</Label>{children}</div>);
}
function Toggle({ label, desc, checked, onChange }: any) {
  const [v, setV] = useState(!!checked);
  return (
    <div className="flex items-center justify-between p-2.5 rounded-lg bg-secondary/40 border border-border/40">
      <div><p className="text-sm font-medium">{label}</p><p className="text-[11px] text-muted-foreground">{desc}</p></div>
      <Switch checked={onChange ? checked : v} onCheckedChange={onChange ?? setV} />
    </div>
  );
}
