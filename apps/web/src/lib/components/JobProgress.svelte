<script lang="ts">
  import { Progress } from "$lib/components/ui/progress/index.js";

  let {
    progress,
    message,
    status,
  }: {
    progress: number;
    message: string;
    status: string;
  } = $props();
</script>

<div class="flex flex-col gap-3">
  <Progress value={progress} max={100} class="h-3" />

  <div class="flex items-center justify-between">
    <p class="text-sm text-muted-foreground">{message}</p>
    <p class="font-mono text-sm">{progress.toFixed(0)}%</p>
  </div>
</div>
