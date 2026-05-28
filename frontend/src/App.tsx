import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppLayout } from "./components/layout/AppLayout";
import Dashboard from "./pages/Dashboard";
import Transcricao from "./pages/Transcricao";
import TextoParaVoz from "./pages/TextoParaVoz";
import Historico from "./pages/Historico";
import Presets from "./pages/Presets";
import Modelos from "./pages/Modelos";
import Diagnostico from "./pages/Diagnostico";
import Configuracoes from "./pages/Configuracoes";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <BrowserRouter>
        <SidebarProvider>
          <Routes>
            <Route element={<AppLayout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/transcricao" element={<Transcricao />} />
              <Route path="/tts" element={<TextoParaVoz />} />
              <Route path="/historico" element={<Historico />} />
              <Route path="/presets" element={<Presets />} />
              <Route path="/modelos" element={<Modelos />} />
              <Route path="/diagnostico" element={<Diagnostico />} />
              <Route path="/configuracoes" element={<Configuracoes />} />
            </Route>
            <Route path="*" element={<NotFound />} />
          </Routes>
        </SidebarProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
