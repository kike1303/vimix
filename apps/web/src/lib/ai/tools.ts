import { tool } from "ai";
import { z } from "zod";
import { fetchProcessors, createJob, createBatch } from "$lib/api";
import type { ChatFile } from "./types";

export function getSystemPrompt(): string {
  return `You are Vimix Assistant, a helpful AI inside the Vimix media processing app. Vimix runs locally on the user's machine — all processing is 100% private, nothing leaves their computer.

Your job is to help users process their files. You can:
1. List available processors and explain what each one does
2. Process files the user has attached to the chat

When the user asks to process a file, use the process_file tool. If they attach multiple files for the same operation, use batch_process.

Always call list_processors first if you need to know what tools are available or to find the right processor for a task. Be concise and friendly. When a tool finishes, tell the user the result and offer to help with more.

If the user hasn't attached a file but asks to process something, ask them to attach the file using the paperclip button.`;
}

export function createTools(attachedFiles: ChatFile[]) {
  return {
    list_processors: tool({
      description:
        "List all available Vimix processors with their descriptions and accepted file types. Call this to discover what processing tools are available.",
      inputSchema: z.object({}),
      execute: async () => {
        const processors = await fetchProcessors();
        return processors
          .map(
            (p) =>
              `**${p.label}** (\`${p.id}\`): ${p.description}\n  Accepts: ${p.accepted_extensions.join(", ")}`,
          )
          .join("\n\n");
      },
    }),
    process_file: tool({
      description:
        "Process a single attached file using a Vimix processor. The file_index refers to the position (0-based) of the file in the user's attached files.",
      inputSchema: z.object({
        processor_id: z
          .string()
          .describe("The processor ID to use (e.g. 'image-bg-remove')"),
        file_index: z
          .number()
          .describe("Index of the attached file to process (0-based)"),
        options: z
          .record(z.string(), z.unknown())
          .optional()
          .describe("Processor-specific options"),
      }),
      execute: async ({
        processor_id,
        file_index,
        options,
      }: {
        processor_id: string;
        file_index: number;
        options?: Record<string, unknown>;
      }) => {
        const file = attachedFiles[file_index];
        if (!file) {
          return `Error: No file at index ${file_index}. The user has ${attachedFiles.length} file(s) attached.`;
        }
        try {
          const job = await createJob(processor_id, file.file, options || {});
          return JSON.stringify({
            success: true,
            jobId: job.id,
            processorId: processor_id,
            filename: file.name,
          });
        } catch (e) {
          return `Error: ${e instanceof Error ? e.message : "Processing failed"}`;
        }
      },
    }),
    batch_process: tool({
      description:
        "Process multiple attached files at once using a single Vimix processor.",
      inputSchema: z.object({
        processor_id: z.string().describe("The processor ID to use"),
        file_indices: z
          .array(z.number())
          .describe("Indices of attached files to process (0-based)"),
        options: z
          .record(z.string(), z.unknown())
          .optional()
          .describe("Processor-specific options"),
      }),
      execute: async ({
        processor_id,
        file_indices,
        options,
      }: {
        processor_id: string;
        file_indices: number[];
        options?: Record<string, unknown>;
      }) => {
        const files = file_indices
          .map((i: number) => attachedFiles[i])
          .filter(Boolean);
        if (files.length === 0) {
          return "Error: No valid files found at the given indices.";
        }
        try {
          const result = await createBatch(
            processor_id,
            files.map((f: ChatFile) => f.file),
            options || {},
          );
          // Use consistent jobId field for tracking/download
          const jobId =
            result.type === "job"
              ? result.id
              : result.job_ids[0];
          return JSON.stringify({
            success: true,
            jobId,
            fileCount: files.length,
          });
        } catch (e) {
          return `Error: ${e instanceof Error ? e.message : "Batch processing failed"}`;
        }
      },
    }),
  };
}
