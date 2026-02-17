<script lang="ts">
  import { goto } from "$app/navigation";
  import { page } from "$app/state";
  import { _ } from "svelte-i18n";
  import {
    fetchProcessors,
    createJob,
    createBatch,
    initApiUrl,
    waitForBackend,
    isTauri,
    type Processor,
  } from "$lib/api";
  import { getProcessorIcon } from "$lib/processor-icons";
  import {
    categories,
    getProcessorsForCategory,
    getCategoryForProcessor,
    getCategoryIcon,
  } from "$lib/processor-categories";
  import * as Alert from "$lib/components/ui/alert/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import ArrowLeft from "lucide-svelte/icons/arrow-left";
  import Loader from "lucide-svelte/icons/loader";
  import CategoryGrid from "$lib/components/CategoryGrid.svelte";
  import ProcessorGrid from "$lib/components/ProcessorGrid.svelte";
  import FileUpload from "$lib/components/FileUpload.svelte";
  import { favoriteIds } from "$lib/stores/favorites.svelte";
  import Heart from "lucide-svelte/icons/heart";
  import Sparkles from "lucide-svelte/icons/sparkles";
  import ArrowRight from "lucide-svelte/icons/arrow-right";
  import Cable from "lucide-svelte/icons/cable";

  let processors = $state<Processor[]>([]);
  let selectedCategory = $state<string | null>(null);
  let selectedProcessor = $state<Processor | null>(null);
  let selectedFiles = $state<File[]>([]);
  let options = $state<Record<string, unknown>>({});
  let uploading = $state(false);
  let error = $state("");

  // Loading state for desktop app startup
  let booting = $state(isTauri());
  let bootFailed = $state(false);

  // Derived: processors filtered by selected category
  let filteredProcessors = $derived(
    selectedCategory
      ? getProcessorsForCategory(processors, selectedCategory)
      : [],
  );

  // Derived: favorite processors
  let favoriteProcessors = $derived(
    processors.filter((p) => favoriteIds.includes(p.id)),
  );

  // Derived: processor counts per category
  let processorCounts = $derived(
    Object.fromEntries(
      categories.map((cat) => [
        cat.id,
        getProcessorsForCategory(processors, cat.id).length,
      ]),
    ),
  );

  $effect(() => {
    let cancelled = false;

    async function init() {
      try {
        // Resolve the API URL (via Tauri IPC or env variable)
        await initApiUrl();

        // In desktop mode, wait until the sidecar is actually ready
        if (isTauri()) {
          await waitForBackend();
          if (cancelled) return;
          booting = false;
        }

        // Fetch the list of processors
        const p = await fetchProcessors();
        if (!cancelled) {
          processors = p;
          error = "";

          // Restore processor from query param (e.g. back from job page)
          const qp = page.url.searchParams.get("processor");
          if (qp) {
            const proc = p.find((pr) => pr.id === qp);
            if (proc) {
              const cat = getCategoryForProcessor(proc.id);
              if (cat) selectedCategory = cat;
              selectProcessor(proc);
            }
            // Clean up the URL
            goto("/", { replaceState: true });
          }
        }
      } catch {
        if (cancelled) return;
        booting = false;
        if (isTauri()) {
          bootFailed = true;
        } else {
          error = $_("upload.errorConnect");
        }
      }
    }

    init();

    return () => {
      cancelled = true;
    };
  });

  function selectCategory(categoryId: string) {
    selectedCategory = categoryId;
    error = "";
  }

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
    if (selectedProcessor) {
      selectedProcessor = null;
      selectedFiles = [];
      options = {};
      error = "";
    } else if (selectedCategory) {
      selectedCategory = null;
      error = "";
    }
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
      if (selectedFiles.length === 1 && !selectedProcessor.accepts_multiple_files) {
        const job = await createJob(selectedProcessor.id, selectedFiles[0], options);
        goto(`/jobs/${job.id}`);
      } else {
        const result = await createBatch(selectedProcessor.id, selectedFiles, options);
        if (result.type === "job") {
          goto(`/jobs/${result.id}`);
        } else {
          goto(`/jobs/batch/${result.id}`);
        }
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

{#if booting}
  <!-- ── Desktop loading screen ── -->
  <div class="flex flex-1 flex-col items-center justify-center gap-4 py-32">
    <div class="flex flex-col items-center gap-3">
      <h1 class="text-3xl font-bold tracking-tight">
        <span class="text-primary">Vi</span>mix
      </h1>
      <Loader class="size-6 animate-spin text-muted-foreground" />
    </div>
    <div class="flex flex-col items-center gap-1">
      <p class="text-sm font-medium text-foreground">{$_("home.loading")}</p>
      <p class="text-xs text-muted-foreground">{$_("home.loadingSub")}</p>
    </div>
  </div>
{:else if bootFailed}
  <!-- ── Desktop boot failure ── -->
  <div class="flex flex-1 flex-col items-center justify-center gap-4 py-32">
    <Alert.Root variant="destructive" class="max-w-md">
      <Alert.Description>{$_("home.loadingFailed")}</Alert.Description>
    </Alert.Root>
  </div>
{:else}
  <div class="flex flex-col gap-6">
    {#if error}
      <Alert.Root variant="destructive">
        <Alert.Description>{error}</Alert.Description>
      </Alert.Root>
    {/if}

    {#if !selectedCategory && !selectedProcessor}
      <!-- ── State 1: Category grid ── -->
      <div class="flex flex-col gap-1">
        <h1 class="text-2xl font-bold">{$_("home.title")}</h1>
        <p class="text-sm text-muted-foreground">{$_("home.subtitle")}</p>
      </div>

      <a
        href="/chat"
        class="group flex items-center gap-3 rounded-xl border border-primary/20 bg-primary/5 px-4 py-3 transition-all hover:border-primary/40 hover:bg-primary/10"
      >
        <div class="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Sparkles class="size-4" />
        </div>
        <p class="flex-1 text-sm font-medium text-foreground">
          {$_("home.chatBanner")}
        </p>
        <ArrowRight class="size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
      </a>

      <div class="flex items-center gap-2.5 rounded-lg px-1 py-1">
        <Cable class="size-3.5 shrink-0 text-muted-foreground" />
        <p class="text-xs text-muted-foreground">
          {$_("home.mcpHint")}
        </p>
      </div>

      <hr class="border-border" />

      {#if favoriteProcessors.length > 0}
        <div class="flex flex-col gap-3">
          <div class="flex items-center gap-2">
            <Heart class="size-4 text-red-500" fill="currentColor" />
            <h2 class="text-sm font-semibold text-foreground">{$_("home.favorites")}</h2>
          </div>
          <ProcessorGrid
            processors={favoriteProcessors}
            onselect={(proc) => selectProcessor(proc)}
          />
        </div>

        <hr class="border-border" />

        <h2 class="text-sm font-semibold text-foreground">{$_("home.categories")}</h2>
      {/if}

      <CategoryGrid {categories} {processorCounts} onselect={selectCategory} />
    {:else if selectedCategory && !selectedProcessor}
      <!-- ── State 2: Processor grid (filtered by category) ── -->
      {@const CatIcon = getCategoryIcon(selectedCategory)}

      <div class="flex items-center gap-3">
        <Button onclick={goBack} variant="ghost" size="icon-sm">
          <ArrowLeft class="size-4" />
        </Button>
        <div class="flex items-center gap-2.5">
          <div class="flex size-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <CatIcon class="size-4" />
          </div>
          <h1 class="text-lg font-bold">{$_(`categories.${selectedCategory}.label`)}</h1>
        </div>
      </div>

      <ProcessorGrid processors={filteredProcessors} onselect={selectProcessor} />
    {:else if selectedProcessor}
      <!-- ── State 3: Tool view ── -->
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
{/if}
