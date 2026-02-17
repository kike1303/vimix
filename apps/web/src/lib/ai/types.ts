export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  files?: ChatFile[];
  toolCalls?: ChatToolCall[];
  createdAt: number;
}

export interface ChatFile {
  name: string;
  size: number;
  type: string;
  file: File;
}

export interface ChatToolCall {
  id: string;
  toolName: string;
  args: Record<string, unknown>;
  status: "pending" | "running" | "completed" | "failed";
  result?: string;
  jobId?: string;
  progress?: number;
  progressMessage?: string;
}

export type ProviderId =
  | "ollama"
  | "openrouter"
  | "anthropic"
  | "openai"
  | "google";

export interface ProviderConfig {
  id: ProviderId;
  name: string;
  apiKey: string;
  baseUrl?: string;
  connected: boolean;
  models: string[];
}

/** Fallback model lists when API fetch fails (e.g. CORS) */
export const FALLBACK_MODELS: Record<ProviderId, string[]> = {
  anthropic: [
    "claude-sonnet-4-5-20250929",
    "claude-haiku-4-5-20251001",
    "claude-opus-4-20250514",
  ],
  openai: ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "o3-mini"],
  google: ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
  openrouter: [
    "anthropic/claude-sonnet-4-5",
    "openai/gpt-4o",
    "google/gemini-2.5-flash",
    "meta-llama/llama-3.3-70b-instruct",
  ],
  ollama: [],
};

export const PROVIDER_DEFAULTS: ProviderConfig[] = [
  {
    id: "anthropic",
    name: "Anthropic",
    apiKey: "",
    connected: false,
    models: [],
  },
  {
    id: "openai",
    name: "OpenAI",
    apiKey: "",
    connected: false,
    models: [],
  },
  {
    id: "google",
    name: "Google Gemini",
    apiKey: "",
    connected: false,
    models: [],
  },
  {
    id: "openrouter",
    name: "OpenRouter",
    apiKey: "",
    baseUrl: "https://openrouter.ai/api/v1",
    connected: false,
    models: [],
  },
  {
    id: "ollama",
    name: "Ollama",
    apiKey: "",
    baseUrl: "http://localhost:11434/v1",
    connected: false,
    models: [],
  },
];

export interface ModelOption {
  providerId: ProviderId;
  providerName: string;
  modelId: string;
}

export interface SelectedModel {
  providerId: ProviderId;
  modelId: string;
}
