import { useEffect, useMemo, useRef, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { StatusPill } from "@/components/shared/StatusPill";
import { Waveform } from "@/components/shared/Waveform";
import { voices as mockVoices, type JobStatus } from "@/lib/mockData";
import { Play, Pause, Sparkles, Wand2, BarChart3, FileJson, FileText, Mic2, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import {
  analyzePtbrText,
  createCompareVoicesJob,
  createTtsGenerateJob,
  createTtsPreviewJob,
  generateVoiceSample,
  getJob,
  getModels,
  getVoiceSamples,
  type ApiJob,
  type ModelVoice,
  type PtbrSuggestion,
  type VoiceSample,
} from "@/lib/api";

const sampleText = "Ola pessoal, hoje eu vou falar sobre inteligencia artificial local e como voce pode usar vozes sinteticas em portugues brasileiro sem depender de APIs pagas. E muito mais simples do que parece, e nao precisa de conexao com a internet.";
const voiceAliasMap: Record<string, string> = {
  dora: "pt_br_dora",
  alex: "pt_br_alex",
  santa: "pt_br_santa",
  faber: "pt_br_faber",
  edresson: "pt_br_edresson",
};

type VoiceCard = {
  id: string;
  alias: string;
  name: string;
  engine: string;
  lang: string;
  style: string;
  status: JobStatus;
  license?: string;
};

type JobKind = "preview" | "generate" | "compare" | "sample";

export default function TextoParaVoz() {
  const [text, setText] = useState(sampleText);
  const [engine, setEngine] = useState("kokoro");
  const [voice, setVoice] = useState("dora");
  const [format, setFormat] = useState("wav");
  const [speed, setSpeed] = useState([1]);
  const [previewChars, setPreviewChars] = useState([200]);
  const [analyze, setAnalyze] = useState(true);
  const [normalizePtbr, setNormalizePtbr] = useState(true);
  const [playing, setPlaying] = useState(false);
  const [playingSampleVoice, setPlayingSampleVoice] = useState<string | null>(null);
  const [issues, setIssues] = useState([
    "O texto tem poucas palavras acentuadas (apenas 1 de 42).",
    "Sugestão: Ola → Olá, voce → você, nao → não, E → É.",
    "3 abreviações detectadas que podem afetar a pronúncia.",
  ]);
  const [previewAudioUrl, setPreviewAudioUrl] = useState<string | null>(null);
  const [previewLogs, setPreviewLogs] = useState<string>("");
  const [compareReportJsonUrl, setCompareReportJsonUrl] = useState<string | null>(null);
  const [compareReportMdUrl, setCompareReportMdUrl] = useState<string | null>(null);
  const [availableVoices, setAvailableVoices] = useState<VoiceCard[]>(mockVoices.map(toVoiceCardFromMock));
  const [voiceSamples, setVoiceSamples] = useState<Record<string, VoiceSample>>({});
  const [usingFallback, setUsingFallback] = useState(false);
  const [currentJob, setCurrentJob] = useState<ApiJob | null>(null);
  const [currentJobKind, setCurrentJobKind] = useState<JobKind | null>(null);
  const previewAudioRef = useRef<HTMLAudioElement | null>(null);
  const sampleAudioRef = useRef<HTMLAudioElement | null>(null);
  const pollTimerRef = useRef<number | null>(null);

  useEffect(() => {
    const loadVoiceData = async () => {
      try {
        const [modelsResponse, samplesResponse] = await Promise.all([getModels(), getVoiceSamples()]);
        const modelVoices = modelsResponse.voices
          .filter((item) => typeof item.alias === "string" && item.alias.startsWith("pt_br_"))
          .map(toVoiceCardFromApi);
        if (modelVoices.length > 0) {
          setAvailableVoices(modelVoices);
        }
        setVoiceSamples(indexSamples(samplesResponse.samples));
        setUsingFallback(false);
      } catch {
        setAvailableVoices(mockVoices.map(toVoiceCardFromMock));
        setUsingFallback(true);
      }
    };

    void loadVoiceData();

    return () => {
      if (pollTimerRef.current) {
        window.clearTimeout(pollTimerRef.current);
      }
    };
  }, []);

  const filteredVoices = availableVoices.filter((v) => v.engine.toLowerCase() === engine);
  const selectedVoice = useMemo(() => filteredVoices.find((item) => item.id === voice), [filteredVoices, voice]);
  const selectedAlias = selectedVoice?.alias || voiceAliasMap[voice] || "pt_br_dora";
  const isBusy = currentJob?.status === "queued" || currentJob?.status === "running";

  const buildPayload = () => ({
    text,
    engine,
    voice: selectedAlias,
    format,
    preview_chars: previewChars[0],
    speed: speed[0],
    normalize_ptbr: normalizePtbr,
    analyze_ptbr: analyze,
    preset: null,
  });

  const extractErrorMessage = (error: unknown) => error instanceof Error ? error.message : "API indisponível.";

  const refreshSamples = async () => {
    try {
      const samplesResponse = await getVoiceSamples();
      setVoiceSamples(indexSamples(samplesResponse.samples));
    } catch {
      // Keep current fallback/sample state silently.
    }
  };

  const pollJobUntilDone = (jobId: string, onSuccess: (job: ApiJob) => void) => {
    const tick = async () => {
      try {
        const job = await getJob(jobId);
        setCurrentJob(job);
        if (job.status === "success") {
          pollTimerRef.current = null;
          onSuccess(job);
          return;
        }
        if (job.status === "error" || job.status === "cancelled") {
          pollTimerRef.current = null;
          toast.error("Job falhou", {
            description: job.error || job.message || "Verifique os logs retornados pela API.",
          });
          return;
        }
        pollTimerRef.current = window.setTimeout(tick, 1500);
      } catch {
        pollTimerRef.current = null;
        toast.error("Falha ao acompanhar job", { description: "A API deixou de responder durante o processamento." });
      }
    };

    void tick();
  };

  const startJob = async (kind: JobKind, createAction: () => Promise<{ job_id: string }>, onSuccess: (job: ApiJob) => void) => {
    try {
      const response = await createAction();
      setCurrentJobKind(kind);
      setCurrentJob({
        job_id: response.job_id,
        type: kind,
        status: "queued",
        stage: "queued",
        progress: 0,
        progress_mode: "indeterminate",
        message: "Job enviado para a API.",
        created_at: new Date().toISOString(),
      });
      pollJobUntilDone(response.job_id, onSuccess);
    } catch (error: unknown) {
      toast.error("Falha ao iniciar job", { description: extractErrorMessage(error) });
    }
  };

  const handleAnalyze = async () => {
    try {
      const response = await analyzePtbrText(text);
      const nextIssues = [
        ...response.analysis.warnings,
        ...response.analysis.suggestions.map((item: PtbrSuggestion) => item.note),
      ];
      setIssues(nextIssues.length > 0 ? nextIssues : ["Nenhum ajuste PT-BR recomendado."]);
      toast.success("Texto analisado");
    } catch {
      toast.info("API offline", { description: "Mantendo sugestões mock do Lovable." });
    }
  };

  const handlePreview = async () => {
    await startJob(
      "preview",
      () => createTtsPreviewJob(buildPayload()),
      (job) => {
        const result = job.result || {};
        if (typeof result.audio_url === "string") {
          setPreviewAudioUrl(result.audio_url);
        }
        if (typeof result.logs === "string") {
          setPreviewLogs(result.logs);
        }
        if (result.analysis && typeof result.analysis === "object") {
          const analysisResult = result.analysis as { warnings?: string[]; suggestions?: PtbrSuggestion[] };
          const nextIssues = [
            ...(analysisResult.warnings || []),
            ...(analysisResult.suggestions || []).map((item) => item.note),
          ];
          if (nextIssues.length > 0) {
            setIssues(nextIssues);
          }
        }
        toast.success("Preview gerado", { description: typeof result.audio_path === "string" ? result.audio_path : "Áudio disponível via API." });
      },
    );
  };

  const handleGenerate = async () => {
    await startJob(
      "generate",
      () => createTtsGenerateJob(buildPayload()),
      (job) => {
        const result = job.result || {};
        if (typeof result.audio_url === "string") {
          setPreviewAudioUrl(result.audio_url);
        }
        if (typeof result.logs === "string") {
          setPreviewLogs(result.logs);
        }
        toast.success("Áudio completo gerado", { description: typeof result.audio_path === "string" ? result.audio_path : "Arquivo pronto em outputs/speech/." });
      },
    );
  };

  const handleCompare = async () => {
    await startJob(
      "compare",
      () => createCompareVoicesJob({ text, language: "pt-br", normalize_ptbr: normalizePtbr }),
      (job) => {
        const result = job.result || {};
        setCompareReportJsonUrl(typeof result.report_json_url === "string" ? result.report_json_url : null);
        setCompareReportMdUrl(typeof result.report_md_url === "string" ? result.report_md_url : null);
        toast.success("Comparativo PT-BR gerado", {
          description: typeof result.output_dir === "string" ? result.output_dir : "Veja os relatórios da API.",
        });
      },
    );
  };

  const handleGenerateSample = async (voiceAlias: string) => {
    await startJob(
      "sample",
      () => generateVoiceSample(voiceAlias),
      async (job) => {
        await refreshSamples();
        const result = job.result || {};
        toast.success("Amostra gerada", {
          description: typeof result.audio_path === "string" ? result.audio_path : `Amostra pronta para ${voiceAlias}.`,
        });
      },
    );
  };

  const togglePreviewPlayback = async () => {
    if (!previewAudioRef.current || !previewAudioUrl) {
      toast.info("Gere um preview primeiro");
      return;
    }
    if (playing) {
      previewAudioRef.current.pause();
      setPlaying(false);
      return;
    }
    await previewAudioRef.current.play();
    setPlaying(true);
  };

  const playVoiceSample = async (voiceAlias: string) => {
    const sample = voiceSamples[voiceAlias];
    if (!sample?.sample_url) {
      void handleGenerateSample(voiceAlias);
      return;
    }

    if (!sampleAudioRef.current) {
      return;
    }

    if (playingSampleVoice === voiceAlias) {
      sampleAudioRef.current.pause();
      setPlayingSampleVoice(null);
      return;
    }

    sampleAudioRef.current.src = sample.sample_url;
    await sampleAudioRef.current.play();
    setPlayingSampleVoice(voiceAlias);
  };

  const jobLogs = currentJob?.logs_tail?.join("\n") || previewLogs;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-bold tracking-tight">Texto para Voz</h1>
            {usingFallback ? <Badge variant="outline" className="text-warning border-warning/30">API offline / dados demonstrativos</Badge> : null}
          </div>
          <p className="text-muted-foreground mt-1">Síntese local com Kokoro e Piper.</p>
        </div>
        <Button variant="outline" disabled={isBusy} onClick={() => { void handleCompare(); }}>
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
              <Button variant="outline" size="sm" disabled={isBusy} onClick={() => { void handlePreview(); }}><Sparkles className="size-4" /> Gerar preview</Button>
              <Button size="sm" disabled={isBusy} className="bg-gradient-to-r from-primary to-accent text-primary-foreground border-0 hover:opacity-90 ml-auto" onClick={() => { void handleGenerate(); }}>
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

          {currentJob ? (
            <Card className="glass-panel p-5">
              <div className="flex items-center justify-between gap-3 mb-3">
                <div>
                  <h3 className="font-semibold">
                    {currentJobKind === "preview" ? "Status do preview" :
                      currentJobKind === "generate" ? "Status da geração" :
                        currentJobKind === "compare" ? "Status do comparativo" : "Status da amostra"}
                  </h3>
                  <p className="text-xs text-muted-foreground">{currentJob.message}</p>
                </div>
                <StatusPill status={toJobStatus(currentJob.status)} />
              </div>
              <Progress value={currentJob.progress_mode === "indeterminate" ? 20 : currentJob.progress} className="h-2" />
              <div className="flex items-center justify-between mt-2 text-[11px] text-muted-foreground">
                <span>Etapa: {currentJob.stage}</span>
                <span>{currentJob.progress_mode === "indeterminate" ? "Aguardando estimativa" : `${currentJob.progress}%`}</span>
              </div>
              {jobLogs ? (
                <div className="mt-3 rounded-lg bg-background/40 border border-border/40 p-3">
                  <p className="text-[11px] font-mono whitespace-pre-wrap line-clamp-6 text-muted-foreground">{jobLogs}</p>
                </div>
              ) : null}
            </Card>
          ) : null}

          <Card className="glass-panel p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">Preview de áudio</h3>
              <Badge variant="outline" className="text-xs">{engine.charAt(0).toUpperCase() + engine.slice(1)} · {selectedVoice?.name || voice} · {speed[0].toFixed(1)}x</Badge>
            </div>
            <div className="flex items-center gap-4">
              <Button size="icon" onClick={() => { void togglePreviewPlayback(); }} className="size-12 rounded-full bg-gradient-to-br from-primary to-accent text-primary-foreground border-0 shadow-[0_0_30px_hsl(var(--primary)/0.4)]">
                {playing ? <Pause className="size-5" /> : <Play className="size-5 ml-0.5" />}
              </Button>
              <div className="flex-1">
                <Waveform active={playing} />
                <div className="flex justify-between text-[11px] font-mono text-muted-foreground mt-1">
                  <span>00:00</span><span>00:14</span>
                </div>
              </div>
            </div>
            <audio ref={previewAudioRef} src={previewAudioUrl || undefined} hidden onEnded={() => setPlaying(false)} onPause={() => setPlaying(false)} />
            <audio ref={sampleAudioRef} hidden onEnded={() => setPlayingSampleVoice(null)} onPause={() => setPlayingSampleVoice(null)} />
            {previewLogs ? <p className="text-[11px] text-muted-foreground mt-3 line-clamp-2">{previewLogs}</p> : null}
          </Card>

          <div>
            <h3 className="font-semibold mb-3">Comparação de vozes PT-BR</h3>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {availableVoices.map((v) => {
                const sample = voiceSamples[v.alias];
                const hasSample = Boolean(sample?.sample_url);
                return (
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
                    <Button variant="ghost" size="sm" disabled={isBusy && !hasSample} className="w-full mt-2 h-8" onClick={() => { void playVoiceSample(v.alias); }}>
                      <Play className="size-3" /> {hasSample ? (playingSampleVoice === v.alias ? "Pausar amostra" : "Tocar amostra") : "Gerar amostra"}
                    </Button>
                  </Card>
                );
              })}
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
              <Select value={engine} onValueChange={(value) => {
                setEngine(value);
                const nextVoice = availableVoices.find((item) => item.engine.toLowerCase() === value);
                if (nextVoice) {
                  setVoice(nextVoice.id);
                }
              }}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem value="kokoro">Kokoro</SelectItem><SelectItem value="piper">Piper</SelectItem></SelectContent>
              </Select>
            </Setting>
            <Setting label="Formato">
              <Select value={format} onValueChange={setFormat}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem value="wav">WAV</SelectItem><SelectItem value="mp3">MP3</SelectItem></SelectContent>
              </Select>
            </Setting>
          </div>

          <Setting label="Voz">
            <Select value={voice} onValueChange={setVoice}>
              <SelectTrigger><SelectValue /></SelectTrigger>
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
            <Toggle label="Normalização PT-BR" desc="Expande abreviações e números" checked={normalizePtbr} onChange={setNormalizePtbr} />
          </div>
        </Card>
      </div>
    </div>
  );
}

function Setting({ label, children }: { label: string; children: React.ReactNode }) {
  return (<div className="space-y-1.5"><Label className="text-xs uppercase tracking-wider text-muted-foreground">{label}</Label>{children}</div>);
}

function Toggle({ label, desc, checked, onChange }: { label: string; desc: string; checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <div className="flex items-center justify-between p-2.5 rounded-lg bg-secondary/40 border border-border/40">
      <div><p className="text-sm font-medium">{label}</p><p className="text-[11px] text-muted-foreground">{desc}</p></div>
      <Switch checked={checked} onCheckedChange={onChange} />
    </div>
  );
}

function toVoiceCardFromMock(voice: typeof mockVoices[number]): VoiceCard {
  return {
    id: voice.id,
    alias: voiceAliasMap[voice.id] || voice.id,
    name: voice.name,
    engine: voice.engine,
    lang: voice.lang,
    style: voice.style,
    status: voice.status,
    license: voice.license,
  };
}

function toVoiceCardFromApi(voice: ModelVoice): VoiceCard {
  const alias = String(voice.alias || "");
  const shortId = alias.replace("pt_br_", "");
  return {
    id: shortId,
    alias,
    name: String(voice.name || shortId),
    engine: capitalize(String(voice.engine || "tts")),
    lang: String(voice.lang || "PT-BR").toUpperCase(),
    style: String(voice.style || "Pronto para teste"),
    status: toVoiceStatus(String(voice.status || "warning")),
  };
}

function indexSamples(samples: VoiceSample[]) {
  return samples.reduce<Record<string, VoiceSample>>((acc, item) => {
    acc[item.voice_alias] = item;
    return acc;
  }, {});
}

function capitalize(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function toVoiceStatus(status: string): JobStatus {
  if (status === "ready") return "ready";
  if (status === "requires_download") return "warning";
  if (status === "missing_dependency" || status === "not_installed") return "missing";
  if (status === "available_with_warning") return "warning";
  return "warning";
}

function toJobStatus(status: string): JobStatus {
  if (status === "queued") return "queued";
  if (status === "running") return "running";
  if (status === "success") return "success";
  if (status === "cancelled") return "warning";
  return "error";
}
