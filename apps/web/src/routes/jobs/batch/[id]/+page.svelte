<script lang="ts">
  import { page } from "$app/state";
  import { _ } from "svelte-i18n";
  import {
    fetchBatch,
    fetchJob,
    subscribeProgress,
    getResultUrl,
    downloadResult,
    type BatchWithJobs,
    type Job,
    type ProgressEvent,
  } from "$lib/api";
  import { toast } from "svelte-sonner";
  import { Button } from "$lib/components/ui/button/index.js";
  import * as Alert from "$lib/components/ui/alert/index.js";
  import { Progress } from "$lib/components/ui/progress/index.js";
  import ArrowLeft from "lucide-svelte/icons/arrow-left";
  import Download from "lucide-svelte/icons/download";
  import BatchJobItem from "$lib/components/BatchJobItem.svelte";
  import JobResult from "$lib/components/JobResult.svelte";

  interface JobState {
    job: Job;
    progress: number;
    message: string;
    status: string;
  }

  let batch = $state<BatchWithJobs | null>(null);
  let jobStates = $state<Map<string, JobState>>(new Map());
  let error = $state("");
  let cleanups: (() => void)[] = [];

  let batchId = $derived(page.params.id as string);

  let jobList = $derived(
    batch ? batch.job_ids.map((id) => jobStates.get(id)).filter(Boolean) as JobState[] : [],
  );
  let completedCount = $derived(jobList.filter((j) => j.status === "completed").length);
  let failedCount = $derived(jobList.filter((j) => j.status === "failed").length);
  let totalCount = $derived(batch?.job_ids.length ?? 0);
  let overallProgress = $derived(
    jobList.length > 0
      ? jobList.reduce((sum, j) => sum + j.progress, 0) / jobList.length
      : 0,
  );
  let allDone = $derived(
    totalCount > 0 && completedCount + failedCount === totalCount,
  );
  let completedJobs = $derived(
    jobList.filter((j) => j.status === "completed"),
  );

  $effect(() => {
    const id = batchId;

    // Clean up previous subscriptions
    for (const cleanup of cleanups) cleanup();
    cleanups = [];

    fetchBatch(id)
      .then((b) => {
        batch = b;

        // Initialize job states
        const states = new Map<string, JobState>();
        for (const job of b.jobs) {
          states.set(job.id, {
            job,
            progress: job.progress,
            message: job.message || $_("job.starting"),
            status: job.status,
          });
        }
        jobStates = states;

        // Subscribe to in-flight jobs
        for (const job of b.jobs) {
          if (job.status === "completed" || job.status === "failed") continue;

          const unsub = subscribeProgress(
            job.id,
            (e: ProgressEvent) => {
              const current = jobStates.get(job.id);
              if (current) {
                jobStates.set(job.id, {
                  ...current,
                  progress: e.progress,
                  message: e.message,
                  status: e.status,
                });
                jobStates = new Map(jobStates);
              }
            },
            () => {
              fetchJob(job.id).then((updated) => {
                const current = jobStates.get(job.id);
                if (current) {
                  jobStates.set(job.id, {
                    job: updated,
                    progress: updated.progress,
                    message: updated.message,
                    status: updated.status,
                  });
                  jobStates = new Map(jobStates);
                }
              });
            },
          );
          cleanups.push(unsub);
        }
      })
      .catch(() => {
        error = $_("batch.notFound");
      });

    return () => {
      for (const cleanup of cleanups) cleanup();
      cleanups = [];
    };
  });

  async function downloadAll() {
    const completed = jobList.filter((j) => j.status === "completed");
    for (const j of completed) {
      const stem = j.job.original_filename.includes(".")
        ? j.job.original_filename.replace(/\.[^.]+$/, "")
        : j.job.original_filename;
      const filename = j.job.result_extension ? `${stem}${j.job.result_extension}` : stem;
      try {
        await downloadResult(j.job.id, filename);
      } catch {
        // individual failures handled silently
      }
    }
    toast.success($_("job.downloadedAll", { values: { count: completed.length } }));
  }
</script>

<svelte:head>
  <title>{$_("batch.title")} – Vimix</title>
</svelte:head>

<div class="flex flex-col gap-6">
  <div class="flex items-center gap-4">
    <Button href={batch ? `/?processor=${batch.processor_id}` : "/"} variant="outline" size="sm" class="gap-1.5">
      <ArrowLeft class="size-4" />
      {$_("batch.backToHome")}
    </Button>
    <h1 class="text-2xl font-bold">
      {#if batch}
        {$_("batch.processing", { values: { count: totalCount } })}
      {:else}
        {$_("job.loading")}
      {/if}
    </h1>
  </div>

  {#if error}
    <Alert.Root variant="destructive">
      <Alert.Description>{error}</Alert.Description>
    </Alert.Root>
  {/if}

  {#if batch}
    <!-- Overall progress -->
    <div class="flex flex-col gap-3">
      <Progress value={overallProgress} max={100} class="h-3" />
      <div class="flex items-center justify-between">
        <p class="text-sm text-muted-foreground">
          {$_("batch.overallProgress", { values: { completed: completedCount, total: totalCount } })}
        </p>
        <p class="font-mono text-sm">{overallProgress.toFixed(0)}%</p>
      </div>
    </div>

    {#if allDone && failedCount > 0}
      <Alert.Root variant="destructive">
        <Alert.Description>
          {$_("batch.someErrors", { values: { count: failedCount } })}
        </Alert.Description>
      </Alert.Root>
    {:else if allDone}
      <Alert.Root>
        <Alert.Description>{$_("batch.allComplete")}</Alert.Description>
      </Alert.Root>
    {/if}

    <!-- Job list -->
    <div class="flex flex-col gap-2 max-h-80 overflow-y-auto">
      {#each jobList as js}
        <BatchJobItem
          jobId={js.job.id}
          filename={js.job.original_filename}
          progress={js.progress}
          message={js.message}
          status={js.status}
          resultExtension={js.job.result_extension}
        />
      {/each}
    </div>

    <!-- Results section when all done -->
    {#if allDone && completedJobs.length > 0}
      <div class="flex flex-col gap-6 border-t border-border pt-6">
        {#each completedJobs as js}
          <div class="flex flex-col gap-2">
            <p class="text-sm font-medium text-muted-foreground">{js.job.original_filename}</p>
            <JobResult
              jobId={js.job.id}
              filename={js.job.original_filename}
              resultExtension={js.job.result_extension || ".webp"}
            />
          </div>
        {/each}

        {#if completedJobs.length > 1}
          <Button size="lg" class="w-full gap-2" onclick={downloadAll}>
            <Download class="size-4" />
            {$_("batch.downloadAll")}
          </Button>
        {/if}
      </div>
    {/if}
  {/if}
</div>
