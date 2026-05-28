import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatusPill } from "@/components/shared/StatusPill";
import { presets, speakerProfiles } from "@/lib/mockData";
import { Plus, Star, Edit, Copy, Trash2, CheckCircle, FileCheck } from "lucide-react";
import { toast } from "sonner";

export default function Presets() {
  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Presets e Perfis</h1>
        <p className="text-muted-foreground mt-1">Configurações reutilizáveis de TTS e mapeamentos de speakers.</p>
      </div>

      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">TTS Presets</h2>
          <Button onClick={() => toast.success("Novo preset criado")}><Plus className="size-4" /> Criar preset</Button>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {presets.map((p) => (
            <Card key={p.id} className="glass-panel p-5 hover:border-primary/40 transition">
              <div className="flex items-start justify-between mb-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-semibold truncate">{p.name}</p>
                    {p.isDefault && <Badge className="bg-primary/15 text-primary border-primary/30 text-[10px]"><Star className="size-2.5 mr-0.5" />Padrão</Badge>}
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">{p.engine} · {p.voice} · {p.format} · {p.speed}x</p>
                </div>
              </div>
              <div className="flex flex-wrap gap-1 mb-4">
                {p.aliases.map((a) => <Badge key={a} variant="outline" className="text-[10px] font-mono">@{a}</Badge>)}
              </div>
              <div className="flex flex-wrap gap-1.5">
                <Button size="sm" variant="outline" className="h-7 text-xs" onClick={() => toast.success(`Preset "${p.name}" aplicado`)}><CheckCircle className="size-3" /> Aplicar</Button>
                {!p.isDefault && <Button size="sm" variant="outline" className="h-7 text-xs"><Star className="size-3" /> Padrão</Button>}
                <Button size="sm" variant="ghost" className="h-7 text-xs"><Edit className="size-3" /></Button>
                <Button size="sm" variant="ghost" className="h-7 text-xs"><Copy className="size-3" /></Button>
                <Button size="sm" variant="ghost" className="h-7 text-xs text-destructive hover:text-destructive"><Trash2 className="size-3" /></Button>
              </div>
            </Card>
          ))}
        </div>
      </section>

      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Perfis de Speakers</h2>
          <Button variant="outline"><Plus className="size-4" /> Novo perfil</Button>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {speakerProfiles.map((p) => (
            <Card key={p.id} className="glass-panel p-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold">{p.name}</h3>
                <StatusPill status="ready" label="Válido" />
              </div>
              <pre className="text-xs font-mono bg-background/60 border border-border/40 rounded-md p-3 overflow-auto leading-relaxed">
{JSON.stringify(p.mapping, null, 2)}
              </pre>
              <div className="flex flex-wrap gap-1.5 mt-4">
                <Button size="sm" variant="outline" className="h-7 text-xs" onClick={() => toast.success(`Perfil "${p.name}" aplicado`)}><CheckCircle className="size-3" /> Aplicar</Button>
                <Button size="sm" variant="ghost" className="h-7 text-xs"><Edit className="size-3" /> Editar</Button>
                <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={() => toast.success("JSON válido")}><FileCheck className="size-3" /> Validar</Button>
                <Button size="sm" variant="ghost" className="h-7 text-xs text-destructive hover:text-destructive"><Trash2 className="size-3" /></Button>
              </div>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
