<script lang="ts">
  import { page } from "$app/state";
  import { _ } from "svelte-i18n";
  import { fetchJob, subscribeProgress, type Job, type ProgressEvent } from "$lib/api";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import * as Alert from "$lib/components/ui/alert/index.js";
  import ArrowLeft from "lucide-svelte/icons/arrow-left";
  import JobProgress from "$lib/components/JobProgress.svelte";
  import JobResult from "$lib/components/JobResult.svelte";

  let job = $state<Job | null>(null);
  let progress = $state(0);
  let message = $state($_("job.starting"));
  let status = $state("pending");
  let error = $state("");

  let jobId = $derived(page.params.id as string);

  $effect(() => {
    const id = jobId;

    fetchJob(id)
      .then((j) => {
        job = j;
        progress = j.progress;
        message = j.message;
        status = j.status;

        if (j.status === "completed" || j.status === "failed") return;

        const unsub = subscribeProgress(
          id,
          (e: ProgressEvent) => {
            progress = e.progress;
            message = e.message;
            status = e.status;
          },
          () => {
            fetchJob(id).then((updated) => {
              job = updated;
              status = updated.status;
              if (updated.error) error = updated.error;
            });
          },
        );

        return unsub;
      })
      .catch(() => {
        error = $_("job.notFound");
      });
  });

  let badgeVariant = $derived(
    status === "completed"
      ? ("default" as const)
      : status === "failed"
        ? ("destructive" as const)
        : ("secondary" as const),
  );
</script>

<svelte:head>
  <title>{$_("job.title")} – Vimix</title>
</svelte:head>

<div class="flex flex-col gap-8">
  <div class="flex items-center gap-4">
    <Button href={job ? `/?processor=${job.processor_id}` : "/"} variant="outline" size="sm" class="gap-1.5">
      <ArrowLeft class="size-4" />
      {$_("job.newJob")}
    </Button>
    <h1 class="text-2xl font-bold">
      {#if job}
        {job.original_filename}
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

  {#if job}
    <div class="flex items-center gap-2">
      <Badge variant={badgeVariant} class="capitalize">{status}</Badge>
    </div>

    {#if status === "processing" || status === "pending"}
      <JobProgress {progress} {message} {status} />
    {/if}

    {#if status === "completed"}
      <JobProgress progress={100} message={$_("job.done")} status="completed" />
      <JobResult jobId={job.id} filename={job.original_filename} resultExtension={job.result_extension || ".webp"} />
    {/if}

    {#if status === "failed"}
      <JobProgress {progress} message={job.error ?? $_("upload.errorUpload")} {status} />
    {/if}
  {/if}
</div>
