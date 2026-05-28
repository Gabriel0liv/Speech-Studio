import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Folder, ShieldCheck, Trash2, Palette, Gauge, History } from "lucide-react";
import { toast } from "sonner";

const paths = [
  { key: "outputs/transcriptions", val: "C:\\SpeechStudio\\outputs\\transcriptions" },
  { key: "outputs/speech", val: "C:\\SpeechStudio\\outputs\\speech" },
  { key: "voices", val: "C:\\SpeechStudio\\voices" },
  { key: "model_cache", val: "C:\\SpeechStudio\\.cache\\models" },
  { key: "tts_cache", val: "C:\\SpeechStudio\\.cache\\tts" },
  { key: "HF_HOME", val: "C:\\Users\\user\\.cache\\huggingface" },
];

export default function Configuracoes() {
  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Configurações</h1>
        <p className="text-muted-foreground mt-1">Preferências locais do Speech Studio.</p>
      </div>

      <Card className="glass-panel p-6">
        <h2 className="font-semibold flex items-center gap-2 mb-4"><Folder className="size-4 text-primary" /> Caminhos locais</h2>
        <div className="space-y-3">
          {paths.map((p) => (
            <div key={p.key} className="grid grid-cols-[180px_1fr_auto] gap-3 items-center">
              <Label className="font-mono text-xs">{p.key}</Label>
              <Input defaultValue={p.val} className="font-mono text-xs bg-background/60" />
              <Button variant="outline" size="sm">Procurar</Button>
            </div>
          ))}
        </div>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="glass-panel p-6">
          <h2 className="font-semibold flex items-center gap-2 mb-4"><History className="size-4 text-primary" /> Privacidade e histórico</h2>
          <div className="space-y-3">
            <Toggle label="Ativar histórico" desc="Salva jobs no SQLite local" defaultChecked />
            <Toggle label="Salvar texto completo" desc="Texto integral no histórico" />
            <Button variant="outline" className="w-full" onClick={() => toast.warning("Histórico limpo", { description: "Saídas preservadas" })}>
              <Trash2 className="size-4" /> Limpar histórico
            </Button>
          </div>
        </Card>

        <Card className="glass-panel p-6">
          <h2 className="font-semibold flex items-center gap-2 mb-4"><Gauge className="size-4 text-primary" /> Performance</h2>
          <div className="space-y-3">
            <Field label="Device padrão">
              <Select defaultValue="cuda"><SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{["auto","cuda","cpu"].map(v=><SelectItem key={v} value={v}>{v}</SelectItem>)}</SelectContent>
              </Select>
            </Field>
            <Field label="Batch size padrão"><Input type="number" defaultValue={16} /></Field>
            <Field label="Compute type padrão">
              <Select defaultValue="float16"><SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{["int8","float16","float32"].map(v=><SelectItem key={v} value={v}>{v}</SelectItem>)}</SelectContent>
              </Select>
            </Field>
          </div>
        </Card>

        <Card className="glass-panel p-6">
          <h2 className="font-semibold flex items-center gap-2 mb-4"><Palette className="size-4 text-primary" /> Tema</h2>
          <div className="space-y-3">
            <Toggle label="Modo escuro" desc="Tema padrão" defaultChecked />
            <Field label="Cor de destaque">
              <div className="flex gap-2">
                {["bg-cyan-500", "bg-violet-500", "bg-emerald-500", "bg-rose-500", "bg-amber-500"].map((c, i) => (
                  <button key={c} className={`size-8 rounded-lg ${c} ring-2 ring-offset-2 ring-offset-background ${i===0 ? "ring-primary" : "ring-transparent"} hover:scale-110 transition`} />
                ))}
              </div>
            </Field>
          </div>
        </Card>

        <Card className="glass-panel p-6 border-primary/30">
          <h2 className="font-semibold flex items-center gap-2 mb-3"><ShieldCheck className="size-4 text-success" /> Segurança</h2>
          <p className="text-sm text-muted-foreground mb-3">Tokens sensíveis nunca são exibidos em texto puro.</p>
          <div className="flex items-center justify-between p-3 rounded-lg bg-background/60 border border-border/40">
            <div>
              <p className="text-sm font-medium">HF Token</p>
              <p className="font-mono text-xs text-muted-foreground">{"•••••••• (não encontrado)"}</p>
            </div>
            <Badge variant="outline" className="text-warning border-warning/30 bg-warning/10">Ausente</Badge>
          </div>
          <Button variant="outline" className="w-full mt-3">Configurar HF_TOKEN</Button>
        </Card>
      </div>
    </div>
  );
}

function Field({ label, children }: any) {
  return <div className="space-y-1.5"><Label className="text-xs uppercase tracking-wider text-muted-foreground">{label}</Label>{children}</div>;
}
function Toggle({ label, desc, defaultChecked }: any) {
  return (
    <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/40 border border-border/40">
      <div><p className="text-sm font-medium">{label}</p><p className="text-xs text-muted-foreground">{desc}</p></div>
      <Switch defaultChecked={defaultChecked} />
    </div>
  );
}
