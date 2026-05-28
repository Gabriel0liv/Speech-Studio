import { NavLink, useLocation } from "react-router-dom";
import {
  LayoutDashboard, FileAudio, Mic, History, Layers, Boxes, Activity, Settings, Waves,
} from "lucide-react";
import {
  Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel,
  SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarHeader, useSidebar,
} from "@/components/ui/sidebar";

const items = [
  { title: "Dashboard", url: "/", icon: LayoutDashboard },
  { title: "Transcrição", url: "/transcricao", icon: FileAudio },
  { title: "Texto para Voz", url: "/tts", icon: Mic },
  { title: "Histórico", url: "/historico", icon: History },
  { title: "Presets e Perfis", url: "/presets", icon: Layers },
  { title: "Modelos e Vozes", url: "/modelos", icon: Boxes },
  { title: "Diagnóstico", url: "/diagnostico", icon: Activity },
  { title: "Configurações", url: "/configuracoes", icon: Settings },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";
  const { pathname } = useLocation();
  const isActive = (path: string) => (path === "/" ? pathname === "/" : pathname.startsWith(path));

  return (
    <Sidebar collapsible="icon" className="border-r border-sidebar-border">
      <SidebarHeader className="border-b border-sidebar-border h-16 flex items-center justify-center px-4">
        <div className="flex items-center gap-2.5 w-full">
          <div className="relative shrink-0">
            <div className="size-9 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-[0_0_20px_hsl(var(--primary)/0.4)]">
              <Waves className="size-5 text-primary-foreground" />
            </div>
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <p className="text-sm font-bold tracking-tight leading-tight">Speech Studio</p>
              <p className="text-[10px] text-muted-foreground uppercase tracking-widest">Local Edition</p>
            </div>
          )}
        </div>
      </SidebarHeader>

      <SidebarContent className="px-2">
        <SidebarGroup>
          {!collapsed && <SidebarGroupLabel>Navegação</SidebarGroupLabel>}
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild isActive={isActive(item.url)} tooltip={item.title}>
                    <NavLink to={item.url} end={item.url === "/"} className="flex items-center gap-3">
                      <item.icon className="size-4 shrink-0" />
                      {!collapsed && <span className="text-sm">{item.title}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
