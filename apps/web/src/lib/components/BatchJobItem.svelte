<script lang="ts">
  import { _ } from "svelte-i18n";
  import { toast } from "svelte-sonner";
  import { getResultUrl, downloadResult } from "$lib/api";
  import { Progress } from "$lib/components/ui/progress/index.js";
  import LoaderCircle from "lucide-svelte/icons/loader-circle";
  import CircleCheck from "lucide-svelte/icons/circle-check";
  import CircleX from "lucide-svelte/icons/circle-x";
  import Download from "lucide-svelte/icons/download";

  let {
    jobId,
    filename,
    progress,
    message,
    status,
    resultExtension = "",
  }: {
    jobId: string;
    filename: string;
    progress: number;
    message: string;
    status: string;
    resultExtension?: string;
  } = $props();

  let resultUrl = $derived(getResultUrl(jobId));
  let stem = $derived(
    filename.includes(".") ? filename.replace(/\.[^.]+$/, "") : filename,
  );
  let downloadName = $derived(
    resultExtension ? `${stem}${resultExtension}` : stem,
  );
</script>

<div class="flex items-center gap-3 rounded-lg border border-border bg-card px-3 py-2.5">
  <!-- Status icon -->
  <div class="shrink-0">
    {#if status === "completed"}
      <CircleCheck class="size-5 text-green-500" />
    {:else if status === "failed"}
      <CircleX class="size-5 text-destructive" />
    {:else}
      <LoaderCircle class="size-5 animate-spin text-muted-foreground" />
    {/if}
  </div>

  <!-- File info + progress -->
  <div class="flex-1 min-w-0 flex flex-col gap-1.5">
    <div class="flex items-center justify-between gap-2">
      <p class="truncate text-sm font-medium">{filename}</p>
      <span class="shrink-0 font-mono text-xs text-muted-foreground">
        {progress.toFixed(0)}%
      </span>
    </div>
    <Progress value={progress} max={100} class="h-1.5" />
  </div>

  <!-- Download link when completed -->
  {#if status === "completed"}
    <button
      type="button"
      onclick={async () => {
        try {
          await downloadResult(jobId, downloadName);
          toast.success($_("job.downloaded", { values: { filename: downloadName } }));
        } catch {
          toast.error($_("job.downloadFailed"));
        }
      }}
      class="shrink-0 rounded-md p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground transition"
      aria-label={$_("job.download")}
    >
      <Download class="size-4" />
    </button>
  {/if}
</div>
