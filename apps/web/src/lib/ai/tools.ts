import { tool } from "ai";
import { z } from "zod";
import { fetchProcessors, createJob, createBatch } from "$lib/api";
import type { ChatFile } from "./types";

export function getSystemPrompt(): string {
  return `You are Vimix Assistant, a helpful AI inside the Vimix media processing app. Vimix runs locally — nothing leaves the user's computer.

## Rules (MUST follow strictly)

1. **List processors first**: ALWAYS call list_processors before processing.
2. **Process ONCE**: Call process_file exactly ONCE per request. NEVER call it twice.
3. **Pass ALL requested options**: When the user specifies values (format, resolution, etc.), you MUST pass ALL of them in the options object. NEVER use defaults when the user gave explicit values. Example: "webp at 256px" → options must be { "format": "webp", "resolution": 256 }.
4. **NEVER ask and execute in the same turn**: Either execute silently OR ask a question — NEVER both. If the request is clear, just do it. If you need clarification, ask and STOP — do NOT process.
5. **Understand options**: "resolution" = output WIDTH in pixels (height auto-scales). NEVER ask about width vs height.
6. **Files persist**: Previously attached files remain available by their original index across the whole conversation.
7. **batch_process**: Only when user attaches multiple files for the same operation.
8. No file attached? Ask them to use the paperclip button.

Be concise. Respond in the same language the user writes in.`;
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
          .map((p) => {
            let text = `**${p.label}** (\`${p.id}\`): ${p.description}\n  Accepts: ${p.accepted_extensions.join(", ")}`;
            if (p.options_schema.length > 0) {
              const opts = p.options_schema.map((o) => {
                let desc = `    - \`${o.id}\` (${o.type}): default=${JSON.stringify(o.default)}`;
                if (o.choices) desc += ` choices=[${o.choices.map((c) => c.value).join(", ")}]`;
                if (o.min != null) desc += ` min=${o.min}`;
                if (o.max != null) desc += ` max=${o.max}`;
                return desc;
              });
              text += `\n  Options:\n${opts.join("\n")}`;
            }
            return text;
          })
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
