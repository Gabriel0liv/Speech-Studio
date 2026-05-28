import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatusPill } from "@/components/shared/StatusPill";
import { engines, voices } from "@/lib/mockData";
import { RefreshCw, BarChart3, FolderOpen, ShieldAlert, Boxes } from "lucide-react";
import { toast } from "sonner";

export default function Modelos() {
  return (
    <div className="space-y-8">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Modelos e Vozes</h1>
          <p className="text-muted-foreground mt-1">Engines instaladas e registro de vozes locais.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => toast.success("Status atualizado")}><RefreshCw className="size-4" /> Atualizar</Button>
          <Button variant="outline" onClick={() => toast.success("Pasta aberta")}><FolderOpen className="size-4" /> Pasta de vozes</Button>
          <Button onClick={() => toast.success("Comparativo gerado")} className="bg-gradient-to-r from-primary to-accent text-primary-foreground border-0"><BarChart3 className="size-4" /> Comparativo PT-BR</Button>
        </div>
      </div>

      <Card className="glass-panel p-4 border-warning/30 flex gap-3 items-start">
        <ShieldAlert className="size-5 text-warning shrink-0 mt-0.5" />
        <div>
          <p className="font-medium text-sm">Verifique as licenças antes de uso comercial</p>
          <p className="text-xs text-muted-foreground mt-0.5">Alguns modelos têm restrições não-comerciais (CC-BY-NC). Sempre confira a licença antes de publicar.</p>
        </div>
      </Card>

      <section>
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2"><Boxes className="size-4 text-primary" /> Engines</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {engines.map((e) => (
            <Card key={e.name} className="glass-panel p-5">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <p className="font-semibold">{e.name}</p>
                  <p className="font-mono text-[11px] text-muted-foreground">v{e.version}</p>
                </div>
                <StatusPill status={e.status} label={e.status === "warning" ? "Requer token" : "Instalado"} />
              </div>
              <p className="text-xs text-muted-foreground">{e.note}</p>
            </Card>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Registro de vozes</h2>
        <Card className="glass-panel overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-secondary/40 text-xs uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="text-left p-3">Voz</th>
                <th className="text-left p-3">Engine</th>
                <th className="text-left p-3">Idioma</th>
                <th className="text-left p-3">Estilo</th>
                <th className="text-left p-3">Licença</th>
                <th className="text-left p-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {voices.map((v) => (
                <tr key={v.id} className="border-t border-border/40 hover:bg-secondary/30 transition">
                  <td className="p-3 font-medium">{v.name}</td>
                  <td className="p-3"><Badge variant="outline" className="text-[10px]">{v.engine}</Badge></td>
                  <td className="p-3 font-mono text-xs">{v.lang}</td>
                  <td className="p-3 text-muted-foreground">{v.style}</td>
                  <td className="p-3"><Badge variant="secondary" className="text-[10px] font-mono">{v.license}</Badge></td>
                  <td className="p-3"><StatusPill status={v.status} label="Baixado · Local" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </section>
    </div>
  );
}
