import { streamText, stepCountIs } from "ai";
import { createProvider } from "$lib/ai/client";
import { createTools, getSystemPrompt } from "$lib/ai/tools";
import { getActiveProvider, ensureTokenFresh } from "$lib/stores/ai-providers.svelte";
import { subscribeProgress, fetchJob } from "$lib/api";
import type { ChatMessage, ChatFile, ChatToolCall } from "$lib/ai/types";

const STORAGE_KEY = "vimix-chat-history";

function loadHistory(): ChatMessage[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const msgs: ChatMessage[] = JSON.parse(raw);
      return msgs.map((m) => ({ ...m, files: undefined }));
    }
  } catch {
    // ignore
  }
  return [];
}

function saveHistory(msgs: ChatMessage[]) {
  try {
    const serializable = msgs.map((m) => ({
      ...m,
      files: m.files?.map((f) => ({ name: f.name, size: f.size, type: f.type })),
    }));
    localStorage.setItem(STORAGE_KEY, JSON.stringify(serializable));
  } catch {
    // storage full, ignore
  }
}

// Use a single state object to avoid "cannot export reassigned $state" error
const chatState = $state({
  messages: loadHistory() as ChatMessage[],
  isStreaming: false,
  attachedFiles: [] as ChatFile[],
});

let abortController: AbortController | null = null;

// Export accessors
export const messages: ChatMessage[] = chatState.messages;
export function getIsStreaming(): boolean {
  return chatState.isStreaming;
}
export const attachedFiles: ChatFile[] = chatState.attachedFiles;

// Reactive derived export for use in components via $derived
export const isStreaming = {
  get current() {
    return chatState.isStreaming;
  },
};

function genId(): string {
  return crypto.randomUUID();
}

function parseApiError(e: unknown): string {
  const msg = e instanceof Error ? e.message : String(e);
  if (/429|too many request/i.test(msg)) {
    return "Rate limit exceeded — too many requests. Wait a moment and try again, or switch to a different model.";
  }
  if (/401|unauthorized|invalid.*key/i.test(msg)) {
    return "Invalid API key. Check your key in the chat settings.";
  }
  if (/403|forbidden/i.test(msg)) {
    return "Access denied. Your API key may not have permission for this model.";
  }
  if (/404|not found/i.test(msg)) {
    return "Model not found. It may have been deprecated — try selecting a different model.";
  }
  if (/500|502|503|504|internal server|bad gateway|service unavailable/i.test(msg)) {
    return "The AI provider is temporarily unavailable. Try again in a moment.";
  }
  if (/network|fetch|ECONNREFUSED|ENOTFOUND/i.test(msg)) {
    return "Could not reach the AI provider. Check your internet connection.";
  }
  return msg;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function attachFile(file: File) {
  chatState.attachedFiles.push({
    name: file.name,
    size: file.size,
    type: file.type,
    file,
  });
}

export function removeFile(index: number) {
  chatState.attachedFiles.splice(index, 1);
}

export function clearChat() {
  chatState.messages.length = 0;
  localStorage.removeItem(STORAGE_KEY);
}

export function stopStreaming() {
  abortController?.abort();
  abortController = null;
  chatState.isStreaming = false;
}

/**
 * Reactively replace the assistant message at the given index.
 * Using full array index assignment guarantees Svelte 5 proxy triggers a re-render.
 */
function flushAssistant(
  idx: number,
  content: string,
  toolCalls: ChatToolCall[],
) {
  const existing = chatState.messages[idx];
  chatState.messages[idx] = {
    ...existing,
    content,
    toolCalls: [...toolCalls],
  };
}

async function trackJobProgress(
  msgIdx: number,
  toolCalls: ChatToolCall[],
  toolCallId: string,
  jobId: string,
): Promise<void> {
  return new Promise<void>((resolve) => {
    subscribeProgress(
      jobId,
      (event) => {
        const tc = toolCalls.find((t) => t.id === toolCallId);
        if (tc) {
          tc.progress = event.progress;
          tc.progressMessage = event.message;
          tc.status = event.status === "failed" ? "failed" : "running";
          flushAssistant(
            msgIdx,
            chatState.messages[msgIdx].content,
            toolCalls,
          );
        }
      },
      async () => {
        try {
          const job = await fetchJob(jobId);
          const tc = toolCalls.find((t) => t.id === toolCallId);
          if (tc) {
            if (job.status === "completed") {
              tc.status = "completed";
              tc.progress = 100;
            } else if (job.status === "failed") {
              tc.status = "failed";
              tc.result = job.error || "Processing failed";
            }
            flushAssistant(
              msgIdx,
              chatState.messages[msgIdx].content,
              toolCalls,
            );
          }
        } catch {
          // ignore
        }
        resolve();
      },
    );
  });
}

export async function sendMessage(content: string) {
  const provider = getActiveProvider();
  if (!provider) return;

  // Auto-refresh OAuth token if needed
  if (provider.config.authType === "oauth") {
    const fresh = await ensureTokenFresh(provider.config.id);
    if (!fresh) {
      // Token expired and refresh failed — add error message
      chatState.messages.push({
        id: genId(),
        role: "assistant",
        content: "",
        error: "Session expired. Please sign in again in the AI settings.",
        createdAt: Date.now(),
      });
      saveHistory([...chatState.messages]);
      return;
    }
  }

  const userFiles = [...chatState.attachedFiles];
  chatState.messages.push({
    id: genId(),
    role: "user",
    content,
    files: userFiles.length > 0 ? userFiles : undefined,
    createdAt: Date.now(),
  });
  chatState.attachedFiles.length = 0;

  chatState.messages.push({
    id: genId(),
    role: "assistant",
    content: "",
    toolCalls: [],
    createdAt: Date.now(),
  });

  const assistantIdx = chatState.messages.length - 1;
  let streamedContent = "";
  const streamedToolCalls: ChatToolCall[] = [];

  chatState.isStreaming = true;
  abortController = new AbortController();

  try {
    const model = createProvider(provider.config, provider.modelId);

    // Collect ALL files from the conversation (not just the current message)
    // so the AI can reference files from earlier messages in follow-ups
    const allFiles: ChatFile[] = [];
    for (const m of chatState.messages) {
      if (m.files) {
        for (const f of m.files) {
          if (f.file) allFiles.push(f);
        }
      }
    }

    const tools = createTools(allFiles);

    // Build AI messages with global file indices that match allFiles order
    let globalFileIdx = 0;
    const aiMessages = chatState.messages.slice(0, -1).map((m) => {
      let text = m.content;
      if (m.files && m.files.length > 0) {
        const validFiles = m.files.filter((f) => f.file);
        if (validFiles.length > 0) {
          const fileList = validFiles
            .map((f) => {
              const line = `  [${globalFileIdx}] ${f.name} (${f.type}, ${formatBytes(f.size)})`;
              globalFileIdx++;
              return line;
            })
            .join("\n");
          text += `\n\n[Attached files:\n${fileList}\n]`;
        }
      }
      return { role: m.role as "user" | "assistant", content: text };
    });

    const systemPrompt = getSystemPrompt();
    const isOAuth = provider.config.authType === "oauth";

    const result = streamText({
      model,
      // ChatGPT backend requires `instructions` instead of system messages
      system: isOAuth ? undefined : systemPrompt,
      messages: aiMessages,
      tools,
      stopWhen: stepCountIs(5),
      abortSignal: abortController?.signal,
      ...(isOAuth && {
        providerOptions: {
          openai: { instructions: systemPrompt, store: false },
        },
      }),
    });

    for await (const part of result.fullStream) {
      if (part.type === "error") {
        throw part.error instanceof Error ? part.error : new Error(String(part.error));
      } else if (part.type === "text-delta") {
        streamedContent += part.text;
        flushAssistant(assistantIdx, streamedContent, streamedToolCalls);
      } else if (part.type === "tool-call") {
        streamedToolCalls.push({
          id: part.toolCallId,
          toolName: part.toolName,
          args: (part.input as Record<string, unknown>) ?? {},
          status: "running",
        });
        flushAssistant(assistantIdx, streamedContent, streamedToolCalls);
      } else if (part.type === "tool-result") {
        const resultStr =
          typeof part.output === "string"
            ? part.output
            : JSON.stringify(part.output);

        const tc = streamedToolCalls.find(
          (t) => t.id === part.toolCallId,
        );
        if (tc) {
          tc.status = "completed";
          tc.result = resultStr;

          // Track job progress if the tool returned a jobId
          try {
            const parsed = JSON.parse(resultStr);
            if (parsed.jobId) {
              tc.jobId = parsed.jobId;
              tc.status = "running";
              tc.progress = 0;
              trackJobProgress(
                assistantIdx,
                streamedToolCalls,
                part.toolCallId,
                parsed.jobId,
              );
            }
          } catch {
            // Not JSON, ignore
          }
        }
        flushAssistant(assistantIdx, streamedContent, streamedToolCalls);
      }
    }
  } catch (e) {
    if ((e as Error).name !== "AbortError") {
      const errorMsg = parseApiError(e);
      const existing = chatState.messages[assistantIdx];
      chatState.messages[assistantIdx] = {
        id: existing.id,
        role: existing.role,
        createdAt: existing.createdAt,
        content: streamedContent || "",
        toolCalls: [...streamedToolCalls],
        error: errorMsg,
      };
    }
  } finally {
    chatState.isStreaming = false;
    abortController = null;
    saveHistory([...chatState.messages]);
  }
}

