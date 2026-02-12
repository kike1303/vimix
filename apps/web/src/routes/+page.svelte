<script lang="ts">
  import { goto } from "$app/navigation";
  import { _ } from "svelte-i18n";
  import {
    fetchProcessors,
    createJob,
    createBatch,
    type Processor,
  } from "$lib/api";
  import { getProcessorIcon } from "$lib/processor-icons";
  import * as Alert from "$lib/components/ui/alert/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import ArrowLeft from "lucide-svelte/icons/arrow-left";
  import ProcessorGrid from "$lib/components/ProcessorGrid.svelte";
  import FileUpload from "$lib/components/FileUpload.svelte";

  let processors = $state<Processor[]>([]);
  let selectedProcessor = $state<Processor | null>(null);
  let selectedFiles = $state<File[]>([]);
  let options = $state<Record<string, unknown>>({});
  let uploading = $state(false);
  let error = $state("");

  $effect(() => {
    fetchProcessors()
      .then((p) => (processors = p))
      .catch(() => (error = $_("upload.errorConnect")));
  });

  function selectProcessor(proc: Processor) {
    selectedProcessor = proc;
    selectedFiles = [];
    const defaults: Record<string, unknown> = {};
    for (const opt of proc.options_schema) {
      defaults[opt.id] = opt.default;
    }
    options = defaults;
    error = "";
  }

  function goBack() {
    selectedProcessor = null;
    selectedFiles = [];
    options = {};
    error = "";
  }

  function procLabel(proc: Processor): string {
    const key = `processors.${proc.id}.label`;
    const translated = $_(key);
    return translated !== key ? translated : proc.label;
  }

  async function handleSubmit() {
    if (!selectedProcessor || selectedFiles.length === 0) return;

    uploading = true;
    error = "";

    try {
      if (selectedFiles.length === 1) {
        const job = await createJob(selectedProcessor.id, selectedFiles[0], options);
        goto(`/jobs/${job.id}`);
      } else {
        const batch = await createBatch(selectedProcessor.id, selectedFiles, options);
        goto(`/jobs/batch/${batch.id}`);
      }
    } catch (e) {
      error = e instanceof Error ? e.message : $_("upload.errorUpload");
      uploading = false;
    }
  }
</script>

<svelte:head>
  <title>Vimix</title>
</svelte:head>

<div class="flex flex-col gap-6">
  {#if error}
    <Alert.Root variant="destructive">
      <Alert.Description>{error}</Alert.Description>
    </Alert.Root>
  {/if}

  {#if !selectedProcessor}
    <!-- ── Grid view ── -->
    <div class="flex flex-col gap-1">
      <h1 class="text-2xl font-bold">{$_("home.title")}</h1>
      <p class="text-sm text-muted-foreground">{$_("home.subtitle")}</p>
    </div>

    <ProcessorGrid {processors} onselect={selectProcessor} />
  {:else}
    <!-- ── Tool view ── -->
    {@const Icon = getProcessorIcon(selectedProcessor.id)}

    <div class="flex items-center gap-3">
      <Button onclick={goBack} variant="ghost" size="icon-sm" disabled={uploading}>
        <ArrowLeft class="size-4" />
      </Button>
      <div class="flex items-center gap-2.5">
        <div class="flex size-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Icon class="size-4" />
        </div>
        <h1 class="text-lg font-bold">{procLabel(selectedProcessor)}</h1>
      </div>
    </div>

    <FileUpload
      processor={selectedProcessor}
      bind:selectedFiles
      bind:options
      onsubmit={handleSubmit}
      disabled={uploading}
    />
  {/if}
</div>
