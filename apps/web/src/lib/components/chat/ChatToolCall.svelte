<script lang="ts">
  import { _ } from "svelte-i18n";
  import { toast } from "svelte-sonner";
  import { getProcessorIcon } from "$lib/processor-icons";
  import { downloadResult } from "$lib/api";
  import type { ChatToolCall } from "$lib/ai/types";
  import Download from "lucide-svelte/icons/download";
  import Loader from "lucide-svelte/icons/loader";
  import Check from "lucide-svelte/icons/check";
  import X from "lucide-svelte/icons/x";
  import List from "lucide-svelte/icons/list";
  import Progress from "$lib/components/ui/progress/progress.svelte";

  let { toolCall }: { toolCall: ChatToolCall } = $props();

  let downloading = $state(false);

  const isProcessing = $derived(
    toolCall.toolName === "process_file" || toolCall.toolName === "batch_process",
  );
  const processorId = $derived(
    isProcessing ? (toolCall.args.processor_id as string) : "",
  );
  const hasResult = $derived(
    toolCall.status === "completed" && !!toolCall.jobId,
  );

  const toolLabel = $derived.by(() => {
    if (toolCall.toolName === "list_processors") return $_("chat.tool.listProcessors");
    if (toolCall.toolName === "process_file") return $_("chat.tool.processFile");
    if (toolCall.toolName === "batch_process") return $_("chat.tool.batchProcess");
    return toolCall.toolName;
  });

  async function handleDownload() {
    if (!toolCall.jobId || downloading) return;
    const filename = `result-${toolCall.jobId.slice(0, 8)}`;
    downloading = true;
    try {
      await downloadResult(toolCall.jobId, filename);
    } catch {
      toast.error($_("job.downloadFailed"));
      downloading = false;
      return;
    }
    downloading = false;
    toast.success($_("job.downloaded", { values: { filename } }));
  }
</script>

<div
  class="my-1.5 flex items-center gap-3 rounded-lg border border-border bg-muted/50 px-3 py-2"
>
  <div class="flex size-8 shrink-0 items-center justify-center rounded-md bg-primary/10">
    {#if isProcessing && processorId}
      {@const Icon = getProcessorIcon(processorId)}
      <Icon class="size-4 text-primary" />
    {:else}
      <List class="size-4 text-primary" />
    {/if}
  </div>

  <div class="min-w-0 flex-1">
    <div class="flex items-center gap-2">
      <span class="text-xs font-medium">{toolLabel}</span>
      {#if toolCall.status === "running"}
        <Loader class="size-3 animate-spin text-muted-foreground" />
      {:else if toolCall.status === "completed"}
        <Check class="size-3 text-green-500" />
      {:else if toolCall.status === "failed"}
        <X class="size-3 text-destructive" />
      {/if}
    </div>

    {#if toolCall.status === "running" && toolCall.progress != null}
      <div class="mt-1 flex items-center gap-2">
        <Progress value={toolCall.progress} class="h-1.5 flex-1" />
        <span class="text-[10px] text-muted-foreground">{Math.round(toolCall.progress)}%</span>
      </div>
      {#if toolCall.progressMessage}
        <p class="mt-0.5 text-[10px] text-muted-foreground">{toolCall.progressMessage}</p>
      {/if}
    {/if}

    {#if toolCall.status === "failed" && toolCall.result}
      <p class="mt-0.5 text-[10px] text-destructive">{toolCall.result}</p>
    {/if}
  </div>

  {#if hasResult}
    <button
      class="flex shrink-0 items-center gap-1.5 rounded-md bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
      onclick={handleDownload}
      disabled={downloading}
      title={$_("job.download")}
    >
      {#if downloading}
        <Loader class="size-3 animate-spin" />
      {:else}
        <Download class="size-3" />
      {/if}
      {$_("job.download")}
    </button>
  {/if}
</div>
