<script lang="ts">
  import { type Processor, extractDimensions } from "$lib/api";
  import { _ } from "svelte-i18n";
  import { Button } from "$lib/components/ui/button/index.js";
  import Upload from "lucide-svelte/icons/upload";
  import X from "lucide-svelte/icons/x";
  import ProcessorOptions from "./ProcessorOptions.svelte";

  let {
    processor,
    selectedFiles = $bindable(),
    options = $bindable(),
    onsubmit,
    disabled = false,
  }: {
    processor: Processor;
    selectedFiles: File[];
    options: Record<string, unknown>;
    onsubmit: () => void;
    disabled?: boolean;
  } = $props();

  let dragover = $state(false);
  let fileInput = $state<HTMLInputElement | null>(null);
  let sourceWidth = $state<number | null>(null);

  $effect(() => {
    if (selectedFiles.length === 0) {
      sourceWidth = null;
      return;
    }
    const files = selectedFiles;
    Promise.all(files.map((f) => extractDimensions(f))).then((results) => {
      const widths = results.filter((r): r is { width: number; height: number } => r !== null).map((r) => r.width);
      sourceWidth = widths.length > 0 ? Math.min(...widths) : null;
    });
  });

  let acceptedExtensions = $derived(
    processor.accepted_extensions.join(","),
  );

  function deduplicateFiles(existing: File[], incoming: File[]): File[] {
    const key = (f: File) => `${f.name}:${f.size}`;
    const seen = new Set(existing.map(key));
    const result = [...existing];
    for (const f of incoming) {
      const k = key(f);
      if (!seen.has(k)) {
        seen.add(k);
        result.push(f);
      }
    }
    return result;
  }

  function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    const valid = Array.from(files).filter((f) => {
      const dot = f.name.lastIndexOf(".");
      if (dot === -1) return false;
      const ext = "." + f.name.slice(dot + 1).toLowerCase();
      return processor.accepted_extensions.includes(ext);
    });
    if (valid.length === 0) return;
    selectedFiles = deduplicateFiles(selectedFiles, valid);
  }

  function removeFile(index: number) {
    selectedFiles = selectedFiles.filter((_, i) => i !== index);
  }

  function handleDrop(e: DragEvent) {
    dragover = false;
    handleFiles(e.dataTransfer?.files ?? null);
  }

  function handleSelect(e: Event) {
    const input = e.target as HTMLInputElement;
    handleFiles(input.files);
    // Reset input so the same file can be re-selected
    input.value = "";
  }

  function formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  }

  let submitLabel = $derived(
    disabled
      ? $_("upload.submitting")
      : selectedFiles.length > 1
        ? $_("upload.submitBatch", { values: { count: selectedFiles.length } })
        : $_("upload.submit"),
  );
</script>

<div class="flex flex-col gap-5">
  <!-- Options panel -->
  {#if processor.options_schema.length > 0}
    <ProcessorOptions
      schema={processor.options_schema}
      bind:values={options}
      {sourceWidth}
      {disabled}
    />
  {/if}

  <!-- Drop zone -->
  <button
    type="button"
    class="relative flex min-h-44 flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed transition
      {dragover
      ? 'border-primary bg-primary/10'
      : 'border-border hover:border-primary/50 hover:bg-accent'}
      {disabled ? 'pointer-events-none opacity-50' : 'cursor-pointer'}"
    ondragover={(e) => {
      e.preventDefault();
      dragover = true;
    }}
    ondragleave={() => (dragover = false)}
    ondrop={(e) => {
      e.preventDefault();
      handleDrop(e);
    }}
    onclick={() => fileInput?.click()}
  >
    <input
      bind:this={fileInput}
      type="file"
      accept={acceptedExtensions}
      multiple
      class="hidden"
      onchange={handleSelect}
      {disabled}
    />

    <Upload class="size-9 text-muted-foreground" />
    <p class="text-sm text-muted-foreground">{$_("upload.dropzone")}</p>
    <p class="text-xs text-muted-foreground">
      {$_("upload.accepted", {
        values: {
          extensions: processor.accepted_extensions.join(", "),
        },
      })}
    </p>
  </button>

  <!-- File list -->
  {#if selectedFiles.length > 0}
    <div class="flex flex-col gap-2">
      {#if selectedFiles.length > 1}
        <p class="text-xs text-muted-foreground">
          {$_("upload.fileCount", { values: { count: selectedFiles.length } })}
        </p>
      {/if}
      {#each selectedFiles as file, i}
        <div class="flex items-center gap-3 rounded-lg border border-border bg-card px-3 py-2">
          <div class="flex-1 min-w-0">
            <p class="truncate text-sm font-medium">{file.name}</p>
            <p class="text-xs text-muted-foreground">{formatSize(file.size)}</p>
          </div>
          <button
            type="button"
            class="shrink-0 rounded-md p-1 text-muted-foreground hover:bg-accent hover:text-foreground transition"
            onclick={(e) => {
              e.stopPropagation();
              removeFile(i);
            }}
            {disabled}
            aria-label={$_("upload.removeFile")}
          >
            <X class="size-4" />
          </button>
        </div>
      {/each}
    </div>

    <!-- Submit -->
    <Button
      size="lg"
      class="w-full"
      onclick={onsubmit}
      {disabled}
    >
      {submitLabel}
    </Button>
  {/if}
</div>
