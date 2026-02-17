import { streamText, stepCountIs } from "ai";
import { createProvider } from "$lib/ai/client";
import { createTools, getSystemPrompt } from "$lib/ai/tools";
import { getActiveProvider } from "$lib/stores/ai-providers.svelte";
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
    const tools = createTools(userFiles);

    const aiMessages = chatState.messages.slice(0, -1).map((m) => {
      let text = m.content;
      // Include file metadata so the AI knows what files the user attached
      if (m.files && m.files.length > 0) {
        const fileList = m.files
          .map((f, i) => `  [${i}] ${f.name} (${f.type}, ${formatBytes(f.size)})`)
          .join("\n");
        text += `\n\n[Attached files:\n${fileList}\n]`;
      }
      return { role: m.role as "user" | "assistant", content: text };
    });

    const result = streamText({
      model,
      system: getSystemPrompt(),
      messages: aiMessages,
      tools,
      stopWhen: stepCountIs(5),
      abortSignal: abortController?.signal,
    });

    for await (const part of result.fullStream) {
      if (part.type === "text-delta") {
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
      const errorMsg = `Error: ${e instanceof Error ? e.message : "Something went wrong"}`;
      streamedContent += streamedContent.length > 0 ? "\n\n" + errorMsg : errorMsg;
      flushAssistant(assistantIdx, streamedContent, streamedToolCalls);
    }
  } finally {
    chatState.isStreaming = false;
    abortController = null;
    saveHistory([...chatState.messages]);
  }
}

