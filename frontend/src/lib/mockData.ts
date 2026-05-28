export const mockStats = {
  transcriptionsToday: 12,
  audiosGenerated: 47,
  modelsAvailable: 8,
  recentJobs: 23,
  storage: "4.7 GB",
};

export type JobStatus = "success" | "warning" | "error" | "running" | "ready" | "missing" | "queued";

export const recentJobs = [
  { id: "1", type: "STT", name: "podcast_ep32.mp3", status: "success" as JobStatus, time: "há 4 min" },
  { id: "2", type: "TTS", name: "intro_narradora_dora.wav", status: "success" as JobStatus, time: "há 18 min" },
  { id: "3", type: "STT", name: "entrevista_cliente.mp4", status: "warning" as JobStatus, time: "há 1 h" },
  { id: "4", type: "TTS", name: "ad_promo_piper_faber.mp3", status: "success" as JobStatus, time: "há 2 h" },
  { id: "5", type: "STT", name: "reuniao_2026_05_27.mkv", status: "error" as JobStatus, time: "há 3 h" },
  { id: "6", type: "TTS", name: "voiceover_demo.wav", status: "success" as JobStatus, time: "ontem" },
];

export const healthChecks = [
  { name: "CUDA / GPU", status: "success" as JobStatus, label: "RTX 4070" },
  { name: "FFmpeg", status: "success" as JobStatus, label: "7.0.2" },
  { name: "eSpeak NG", status: "success" as JobStatus, label: "1.52" },
  { name: "Kokoro", status: "success" as JobStatus, label: "Pronto" },
  { name: "Piper", status: "success" as JobStatus, label: "Pronto" },
  { name: "WhisperX", status: "success" as JobStatus, label: "v3.1.5" },
  { name: "Pyannote", status: "warning" as JobStatus, label: "Token HF" },
];

export const voices = [
  { id: "dora", name: "Dora", engine: "Kokoro", lang: "PT-BR", style: "Narradora feminina", status: "ready" as JobStatus, license: "Apache-2.0" },
  { id: "alex", name: "Alex", engine: "Kokoro", lang: "PT-BR", style: "Narrador masculino", status: "ready" as JobStatus, license: "Apache-2.0" },
  { id: "santa", name: "Santa", engine: "Kokoro", lang: "PT-BR", style: "Voz quente e calma", status: "ready" as JobStatus, license: "Apache-2.0" },
  { id: "faber", name: "Faber", engine: "Piper", lang: "PT-BR", style: "Masculino neutro", status: "ready" as JobStatus, license: "MIT" },
  { id: "edresson", name: "Edresson", engine: "Piper", lang: "PT-BR", style: "Masculino expressivo", status: "ready" as JobStatus, license: "CC-BY" },
];

export const presets = [
  { id: "1", name: "Narradora Kokoro Dora", engine: "Kokoro", voice: "Dora", format: "WAV", speed: 1.0, isDefault: true, aliases: ["narradora", "default-f"] },
  { id: "2", name: "Narrador Kokoro Alex", engine: "Kokoro", voice: "Alex", format: "WAV", speed: 1.0, isDefault: false, aliases: ["narrador"] },
  { id: "3", name: "Narrador Kokoro Santa", engine: "Kokoro", voice: "Santa", format: "MP3", speed: 0.95, isDefault: false, aliases: ["calmo"] },
  { id: "4", name: "Piper Faber", engine: "Piper", voice: "Faber", format: "WAV", speed: 1.0, isDefault: false, aliases: ["rapido"] },
  { id: "5", name: "Piper Edresson", engine: "Piper", voice: "Edresson", format: "MP3", speed: 1.05, isDefault: false, aliases: ["expressivo"] },
];

export const speakerProfiles = [
  { id: "podcast", name: "Podcast", mapping: { SPEAKER_00: "Gabriell", SPEAKER_01: "Pessoa 2" } },
  { id: "entrevista", name: "Entrevista", mapping: { SPEAKER_00: "Entrevistador", SPEAKER_01: "Convidado" } },
  { id: "reuniao", name: "Reunião", mapping: { SPEAKER_00: "Gabriell", SPEAKER_01: "Cliente A", SPEAKER_02: "Cliente B" } },
];

export const engines = [
  { name: "WhisperX", status: "ready" as JobStatus, version: "3.1.5", note: "Transcrição com alinhamento" },
  { name: "Pyannote", status: "warning" as JobStatus, version: "3.1", note: "Requer token Hugging Face" },
  { name: "Kokoro", status: "ready" as JobStatus, version: "82M v1.0", note: "TTS leve e natural" },
  { name: "Piper", status: "ready" as JobStatus, version: "1.2.0", note: "TTS rápido offline" },
  { name: "FFmpeg", status: "ready" as JobStatus, version: "7.0.2", note: "Conversão de mídia" },
  { name: "eSpeak NG", status: "ready" as JobStatus, version: "1.52", note: "Fonemizador" },
];

export const transcriptPreview = [
  { time: "00:00:02", speaker: "Gabriell", text: "Olá, bem-vindo ao episódio de hoje do podcast." },
  { time: "00:00:07", speaker: "Gabriell", text: "Vamos falar sobre IA local e privacidade de dados." },
  { time: "00:00:14", speaker: "Pessoa 2", text: "Obrigado pelo convite. É um tema que me apaixona." },
  { time: "00:00:21", speaker: "SPEAKER_00", text: "Antes de começar, queria contextualizar nossos ouvintes..." },
  { time: "00:00:30", speaker: "Pessoa 2", text: "Claro, fique à vontade. Acho importante alinharmos." },
];

export const diagnosticLines = [
  { type: "info" as const, text: "› speech-studio-local healthcheck v1.4.2" },
  { type: "info" as const, text: "› Iniciando verificação completa..." },
  { type: "ok" as const, text: "[OK]   Python 3.11.7 (64-bit)" },
  { type: "ok" as const, text: "[OK]   CUDA 12.4 — NVIDIA GeForce RTX 4070 (12 GB)" },
  { type: "ok" as const, text: "[OK]   FFmpeg 7.0.2 — encontrado em PATH" },
  { type: "ok" as const, text: "[OK]   eSpeak NG 1.52 — fonemizador disponível" },
  { type: "ok" as const, text: "[OK]   Hugging Face cache: C:\\Users\\user\\.cache\\huggingface (2.3 GB)" },
  { type: "warn" as const, text: "[WARN] HF_TOKEN: não encontrado — pyannote pode falhar" },
  { type: "ok" as const, text: "[OK]   outputs/transcriptions — gravável" },
  { type: "ok" as const, text: "[OK]   outputs/speech — gravável" },
  { type: "ok" as const, text: "[OK]   SQLite history.db — 187 registros, 4.2 MB" },
  { type: "ok" as const, text: "[OK]   WhisperX 3.1.5 carregado" },
  { type: "ok" as const, text: "[OK]   Kokoro 82M v1.0 — vozes: dora, alex, santa" },
  { type: "ok" as const, text: "[OK]   Piper 1.2.0 — vozes: faber, edresson" },
  { type: "info" as const, text: "› Diagnóstico concluído em 2.41s" },
];
