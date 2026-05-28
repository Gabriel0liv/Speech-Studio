export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

export type HealthResponse = {
  success: boolean;
  python_version: string;
  project_root: string;
  packages: Array<{ label: string; installed: boolean; status: string; critical: boolean }>;
  cuda: { status: string; available: boolean; gpu_name: string };
  ffmpeg: { available: boolean };
  espeak: { available: boolean; path?: string | null };
  huggingface: { token_configured: boolean; token_status: string; hf_home: string; offline_mode: boolean };
  directories: Array<{ name: string; path: string; exists: boolean; status: string }>;
};

export type HistoryJob = Record<string, unknown> & {
  id: string | number;
  job_type?: string;
  type?: string;
  input_name?: string;
  name?: string;
  status?: string;
  created_at?: string;
  time?: string;
  file_url?: string | null;
};

export type Preset = Record<string, unknown>;
export type SpeakerProfile = Record<string, unknown>;
export type ModelVoice = Record<string, unknown>;
export type ApiEngine = Record<string, unknown>;
export type PtbrSuggestion = { original: string; suggested: string; note: string };
export type PtbrAnalysis = { warnings: string[]; suggestions: PtbrSuggestion[]; has_issues: boolean };

export type TtsRequest = {
  text: string;
  engine: string;
  voice: string;
  format: string;
  preview_chars?: number;
  speed?: number;
  normalize_ptbr?: boolean;
  analyze_ptbr?: boolean;
  preset?: string | null;
};

export type TtsResponse = {
  success: boolean;
  audio_path?: string | null;
  audio_url?: string | null;
  analysis?: PtbrAnalysis;
  logs?: string;
  stdout?: string;
  stderr?: string;
  returncode?: number;
  error?: string | null;
};

async function parseResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get("content-type") || "";
  const payload: unknown = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail =
      typeof payload === "string"
        ? payload
        : (payload as { detail?: string; error?: string }).detail ||
          (payload as { detail?: string; error?: string }).error ||
          "Falha ao comunicar com a API.";
    throw new Error(detail);
  }

  return payload as T;
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  return parseResponse<T>(response);
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseResponse<T>(response);
}

export function getHealth() {
  return getJson<HealthResponse>("/health");
}

export async function getHistory() {
  const response = await getJson<{ success: boolean; jobs: HistoryJob[] }>("/history");
  return response.jobs;
}

export async function getPresets() {
  const response = await getJson<{ success: boolean; presets: Preset[] }>("/presets");
  return response.presets;
}

export async function getSpeakerProfiles() {
  const response = await getJson<{ success: boolean; speaker_profiles: SpeakerProfile[] }>("/speaker-profiles");
  return response.speaker_profiles;
}

export async function getModels() {
  return getJson<{ success: boolean; engines: ApiEngine[]; voices: ModelVoice[] }>("/models");
}

export function analyzePtbrText(text: string, language = "pt-br") {
  return postJson<{ success: boolean; analysis: PtbrAnalysis }>("/tts/analyze-text", { text, language });
}

export function generateTtsPreview(payload: TtsRequest) {
  return postJson<TtsResponse>("/tts/preview", payload);
}

export function generateTtsFull(payload: TtsRequest) {
  return postJson<TtsResponse>("/tts/generate", payload);
}

export function compareVoices(payload: { text?: string; language?: string; normalize_ptbr?: boolean }) {
  return postJson<Record<string, unknown>>("/tts/compare-voices", payload);
}

export async function transcribeFile(formData: FormData) {
  const response = await fetch(`${API_BASE_URL}/stt/transcribe`, {
    method: "POST",
    body: formData,
  });
  return parseResponse<Record<string, unknown>>(response);
}
