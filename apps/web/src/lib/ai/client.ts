import { createOpenAI } from "@ai-sdk/openai";
import { createAnthropic } from "@ai-sdk/anthropic";
import { createGoogleGenerativeAI } from "@ai-sdk/google";
import type { ProviderConfig } from "./types";

export function createProvider(config: ProviderConfig, modelId: string) {
  switch (config.id) {
    case "anthropic": {
      const anthropic = createAnthropic({
        apiKey: config.apiKey,
      });
      return anthropic(modelId);
    }
    case "google": {
      const google = createGoogleGenerativeAI({
        apiKey: config.apiKey,
      });
      return google(modelId);
    }
    case "ollama":
    case "openrouter": {
      const openai = createOpenAI({
        apiKey: config.apiKey || "ollama",
        baseURL: config.baseUrl,
      });
      return openai(modelId);
    }
    case "openai": {
      if (config.authType === "oauth") {
        // ChatGPT subscription tokens use the ChatGPT backend, not api.openai.com
        const openai = createOpenAI({
          apiKey: config.apiKey,
          baseURL: "https://chatgpt.com/backend-api/codex",
        });
        return openai.responses(modelId);
      }
      const openai = createOpenAI({
        apiKey: config.apiKey,
      });
      return openai(modelId);
    }
    default:
      throw new Error(`Unknown provider: ${config.id}`);
  }
}
