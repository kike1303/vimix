<script lang="ts">
  import type { Processor } from "$lib/api";
  import { _ } from "svelte-i18n";
  import { Button } from "$lib/components/ui/button/index.js";
  import Upload from "lucide-svelte/icons/upload";
  import CircleCheck from "lucide-svelte/icons/circle-check";
  import ProcessorOptions from "./ProcessorOptions.svelte";

  let {
    processor,
    selectedFile = $bindable(),
    options = $bindable(),
    onsubmit,
    disabled = false,
  }: {
    processor: Processor;
    selectedFile: File | null;
    options: Record<string, unknown>;
    onsubmit: () => void;
    disabled?: boolean;
  } = $props();

  let dragover = $state(false);
  let fileInput = $state<HTMLInputElement | null>(null);

  let acceptedExtensions = $derived(
    processor.accepted_extensions.join(","),
  );

  function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    selectedFile = files[0];
  }

  function handleDrop(e: DragEvent) {
    dragover = false;
    handleFiles(e.dataTransfer?.files ?? null);
  }

  function handleSelect(e: Event) {
    const input = e.target as HTMLInputElement;
    handleFiles(input.files);
  }
</script>

<div class="flex flex-col gap-5">
  <!-- Options panel -->
  {#if processor.options_schema.length > 0}
    <ProcessorOptions
      schema={processor.options_schema}
      bind:values={options}
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
      class="hidden"
      onchange={handleSelect}
      {disabled}
    />

    {#if selectedFile}
      <CircleCheck class="size-9 text-green-500" />
      <p class="text-sm font-medium">{selectedFile.name}</p>
      <p class="text-xs text-muted-foreground">
        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB &ndash;
        {$_("upload.changeFile")}
      </p>
    {:else}
      <Upload class="size-9 text-muted-foreground" />
      <p class="text-sm text-muted-foreground">{$_("upload.dropzone")}</p>
      <p class="text-xs text-muted-foreground">
        {$_("upload.accepted", {
          values: {
            extensions: processor.accepted_extensions.join(", "),
          },
        })}
      </p>
    {/if}
  </button>

  <!-- Submit -->
  {#if selectedFile}
    <Button
      size="lg"
      class="w-full"
      onclick={onsubmit}
      {disabled}
    >
      {disabled ? $_("upload.submitting") : $_("upload.submit")}
    </Button>
  {/if}
</div>
