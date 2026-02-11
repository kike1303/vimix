<script lang="ts">
  import { getResultUrl } from "$lib/api";
  import { _ } from "svelte-i18n";
  import { Button } from "$lib/components/ui/button/index.js";
  import Download from "lucide-svelte/icons/download";
  import FileArchive from "lucide-svelte/icons/file-archive";
  import FileVideo from "lucide-svelte/icons/file-video";

  let {
    jobId,
    filename,
    resultExtension = ".webp",
  }: {
    jobId: string;
    filename: string;
    resultExtension?: string;
  } = $props();

  let resultUrl = $derived(getResultUrl(jobId));

  let stem = $derived(
    filename.includes(".")
      ? filename.replace(/\.[^.]+$/, "")
      : filename,
  );

  let downloadName = $derived(`${stem}${resultExtension}`);

  const PREVIEWABLE = new Set([".webp", ".gif", ".png", ".jpg", ".bmp"]);
  let previewable = $derived(PREVIEWABLE.has(resultExtension));
</script>

<div class="flex flex-col items-center gap-6">
  {#if previewable}
    <!-- Preview (checkerboard background to show transparency) -->
    <div
      class="overflow-hidden rounded-xl border border-border"
      style="background-image: repeating-conic-gradient(
        var(--muted) 0% 25%, var(--card) 0% 50%
      ); background-size: 20px 20px;"
    >
      <img
        src={resultUrl}
        alt="Result preview"
        class="max-h-96 max-w-full object-contain"
      />
    </div>
  {:else}
    <!-- Non-previewable format: show icon + filename -->
    <div class="flex flex-col items-center gap-3 rounded-xl border border-border bg-card p-10">
      {#if resultExtension === ".zip"}
        <FileArchive class="size-16 text-muted-foreground" />
      {:else}
        <FileVideo class="size-16 text-muted-foreground" />
      {/if}
      <p class="text-sm font-medium text-card-foreground">{downloadName}</p>
      <p class="text-xs text-muted-foreground">{$_("job.readyToDownload")}</p>
    </div>
  {/if}

  <Button href={resultUrl} size="lg" class="gap-2">
    <Download class="size-4" />
    {$_("job.download")} {downloadName}
  </Button>
</div>
