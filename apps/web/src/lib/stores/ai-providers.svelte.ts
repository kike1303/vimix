import { browser } from "$app/environment";
import {
  PROVIDER_DEFAULTS,
  FALLBACK_MODELS,
  type ProviderId,
  type ProviderConfig,
  type ModelOption,
  type SelectedModel,
} from "$lib/ai/types";

const PROVIDERS_KEY = "vimix-ai-providers";
const MODEL_KEY = "vimix-selected-model";

// ── Persistence ────────────────────────────────────────────────

function loadProviders(): ProviderConfig[] {
  if (!browser) return structuredClone(PROVIDER_DEFAULTS);
  try {
    const raw = localStorage.getItem(PROVIDERS_KEY);
    if (raw) {
      const saved: ProviderConfig[] = JSON.parse(raw);
      return PROVIDER_DEFAULTS.map((def) => {
        const existing = saved.find((s) => s.id === def.id);
        return existing ? { ...def, ...existing } : { ...def };
      });
    }
  } catch {
    // ignore corrupt data
  }
  return structuredClone(PROVIDER_DEFAULTS);
}

function saveProviders(configs: ProviderConfig[]) {
  if (!browser) return;
  localStorage.setItem(PROVIDERS_KEY, JSON.stringify(configs));
}

function loadSelectedModel(): SelectedModel | null {
  if (!browser) return null;
  try {
    const raw = localStorage.getItem(MODEL_KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    // ignore
  }
  return null;
}

function saveSelectedModel(model: SelectedModel | null) {
  if (!browser) return;
  if (model) {
    localStorage.setItem(MODEL_KEY, JSON.stringify(model));
  } else {
    localStorage.removeItem(MODEL_KEY);
  }
}

// ── State ──────────────────────────────────────────────────────

export let providers: ProviderConfig[] = $state(loadProviders());

const _selectedModel = $state<{ value: SelectedModel | null }>({
  value: loadSelectedModel(),
});

export const selectedModel = {
  get current(): SelectedModel | null {
    return _selectedModel.value;
  },
};

export function setSelectedModel(model: SelectedModel | null) {
  _selectedModel.value = model;
  saveSelectedModel(model);
}

// ── Provider helpers ───────────────────────────────────────────

export function updateProvider(id: ProviderId, updates: Partial<ProviderConfig>) {
  const idx = providers.findIndex((p) => p.id === id);
  if (idx < 0) return;
  providers[idx] = { ...providers[idx], ...updates };
  saveProviders([...providers]);
}

export function getConnectedProviders(): ProviderConfig[] {
  return providers.filter((p) => p.connected && p.models.length > 0);
}

export function getAllAvailableModels(): ModelOption[] {
  const result: ModelOption[] = [];
  for (const p of providers) {
    if (!p.connected || p.models.length === 0) continue;
    for (const modelId of p.models) {
      result.push({
        providerId: p.id,
        providerName: p.name,
        modelId,
      });
    }
  }
  return result;
}

/** Get the active ProviderConfig + modelId for the chat */
export function getActiveProvider(): { config: ProviderConfig; modelId: string } | null {
  const sel = _selectedModel.value;
  if (!sel) return null;
  const provider = providers.find((p) => p.id === sel.providerId);
  if (!provider || !provider.connected) return null;
  return { config: provider, modelId: sel.modelId };
}

// ── Model fetching ─────────────────────────────────────────────

async function fetchOpenAICompatModels(
  apiKey: string,
  baseUrl: string,
  filter?: (id: string) => boolean,
): Promise<string[]> {
  const res = await fetch(`${baseUrl}/models`, {
    headers: apiKey ? { Authorization: `Bearer ${apiKey}` } : {},
  });
  if (!res.ok) return [];
  const data = await res.json();
  let models: string[] = (data.data || []).map((m: { id: string }) => m.id);
  if (filter) models = models.filter(filter);
  return models.sort();
}

async function fetchAnthropicModels(apiKey: string): Promise<string[]> {
  const res = await fetch("https://api.anthropic.com/v1/models", {
    headers: {
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
    },
  });
  if (!res.ok) return [];
  const data = await res.json();
  const all: string[] = (data.data || [])
    .map((m: { id: string }) => m.id)
    .filter((id: string) => id.includes("claude"));
  // Keep only latest gen (claude-{family}-X format), skip old claude-3-* naming
  const latest = all.filter((id) => /^claude-(sonnet|haiku|opus)-\d/.test(id));
  return latest.length > 0 ? latest.sort() : all.sort();
}

/**
 * Fetch Google models, then keep only the latest stable version per family (flash/pro).
 * e.g. if both gemini-2.0-flash and gemini-2.5-flash exist, only gemini-2.5-flash is kept.
 */
async function fetchGoogleModels(apiKey: string): Promise<string[]> {
  const res = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`,
  );
  if (!res.ok) return [];
  const data = await res.json();
  const all: string[] = (data.models || [])
    .map((m: { name: string }) => m.name.replace("models/", ""));

  // Only consider stable base models: gemini-X.Y-flash / gemini-X.Y-pro (no suffixes)
  const stable = all.filter((id) => /^gemini-\d+\.\d+-(flash|pro)$/.test(id));

  // Group by family and keep only the highest version
  const best: Record<string, { major: number; minor: number; id: string }> = {};
  for (const id of stable) {
    const m = id.match(/^gemini-(\d+)\.(\d+)-(flash|pro)$/);
    if (!m) continue;
    const major = parseInt(m[1]);
    const minor = parseInt(m[2]);
    const family = m[3];
    const prev = best[family];
    if (!prev || major > prev.major || (major === prev.major && minor > prev.minor)) {
      best[family] = { major, minor, id };
    }
  }
  return Object.values(best).map((f) => f.id).sort().reverse();
}

async function fetchOllamaModels(): Promise<string[]> {
  const res = await fetch("http://localhost:11434/api/tags");
  if (!res.ok) return [];
  const data = await res.json();
  return (data.models || []).map((m: { name: string }) => m.name);
}

export async function fetchModelsForProvider(config: ProviderConfig): Promise<string[]> {
  try {
    switch (config.id) {
      case "openai":
        return await fetchOpenAICompatModels(
          config.apiKey,
          "https://api.openai.com/v1",
          // Keep gpt-*/o*/chatgpt-* but exclude dated variants (YYYY-MM-DD)
          (id) => /^(gpt-|o[0-9]|chatgpt-)/.test(id) && !/\d{4}-\d{2}-\d{2}/.test(id),
        );
      case "anthropic":
        return await fetchAnthropicModels(config.apiKey);
      case "google":
        return await fetchGoogleModels(config.apiKey);
      case "openrouter":
        return await fetchOpenAICompatModels(
          config.apiKey,
          "https://openrouter.ai/api/v1",
          // OpenRouter has thousands — filter to popular ones
          (id) =>
            /^(anthropic|openai|google|meta-llama|mistralai|deepseek)\//.test(id),
        );
      case "ollama":
        return await fetchOllamaModels();
      default:
        return [];
    }
  } catch {
    // CORS or network error — use fallback
    return FALLBACK_MODELS[config.id] || [];
  }
}

// ── Connect / Disconnect ───────────────────────────────────────

export async function connectProvider(
  id: ProviderId,
): Promise<{ success: boolean; models: string[] }> {
  const provider = providers.find((p) => p.id === id);
  if (!provider) return { success: false, models: [] };

  // For Ollama, no API key needed — just check if it's running
  if (id === "ollama") {
    const models = await fetchModelsForProvider(provider);
    if (models.length > 0) {
      updateProvider(id, { connected: true, models });
      autoSelectFirstModel(id, models);
      return { success: true, models };
    }
    updateProvider(id, { connected: false, models: [] });
    return { success: false, models: [] };
  }

  // For API key providers: fetch models from API (validates the key)
  if (!provider.apiKey) return { success: false, models: [] };

  let models = await fetchModelsForProvider(provider);

  // If fetch returned empty (CORS, etc.), test key with a real call + use fallback list
  if (models.length === 0) {
    const fallback = FALLBACK_MODELS[id] || [];
    try {
      const { createProvider } = await import("$lib/ai/client");
      const { generateText } = await import("ai");
      if (!fallback[0]) return { success: false, models: [] };
      const model = createProvider({ ...provider }, fallback[0]);
      await generateText({ model, prompt: "Say OK", maxOutputTokens: 5 });
      models = fallback;
    } catch {
      updateProvider(id, { connected: false, models: [] });
      return { success: false, models: [] };
    }
  }

  updateProvider(id, { connected: true, models });
  autoSelectFirstModel(id, models);
  return { success: true, models };
}

function autoSelectFirstModel(providerId: ProviderId, models: string[]) {
  // If no model is selected yet, auto-select the first one
  if (!_selectedModel.value && models.length > 0) {
    setSelectedModel({ providerId, modelId: models[0] });
  }
}

export function disconnectProvider(id: ProviderId) {
  updateProvider(id, { connected: false, models: [], apiKey: "" });
  // If the disconnected provider was selected, clear selection
  if (_selectedModel.value?.providerId === id) {
    // Try to select another connected provider
    const other = providers.find((p) => p.connected && p.models.length > 0 && p.id !== id);
    if (other) {
      setSelectedModel({ providerId: other.id, modelId: other.models[0] });
    } else {
      setSelectedModel(null);
    }
  }
  saveProviders([...providers]);
}

export async function detectOllama(): Promise<boolean> {
  try {
    const models = await fetchOllamaModels();
    if (models.length > 0) {
      updateProvider("ollama", { connected: true, models });
      autoSelectFirstModel("ollama", models);
      return true;
    }
  } catch {
    // not running
  }
  return false;
}
