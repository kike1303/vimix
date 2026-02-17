<script lang="ts">
  import { _ } from "svelte-i18n";
  import {
    isStreaming,
    attachedFiles,
    attachFile,
    removeFile,
    stopStreaming,
  } from "$lib/stores/chat.svelte";
  import { getActiveProvider } from "$lib/stores/ai-providers.svelte";
  import Paperclip from "lucide-svelte/icons/paperclip";
  import Send from "lucide-svelte/icons/send";
  import Square from "lucide-svelte/icons/square";
  import X from "lucide-svelte/icons/x";

  let { onsend }: { onsend: (text: string) => void } = $props();

  let input = $state("");
  let textarea: HTMLTextAreaElement | undefined = $state();
  let fileInput: HTMLInputElement | undefined = $state();

  const provider = $derived(getActiveProvider());
  const streaming = $derived(isStreaming.current);
  const canSend = $derived(input.trim().length > 0 && provider && !streaming);

  function handleSend() {
    if (!canSend) return;
    onsend(input.trim());
    input = "";
    if (textarea) {
      textarea.style.height = "auto";
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleInput() {
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = Math.min(textarea.scrollHeight, 160) + "px";
  }

  function handleFileSelect(e: Event) {
    const target = e.target as HTMLInputElement;
    if (target.files) {
      for (const file of target.files) {
        attachFile(file);
      }
      target.value = "";
    }
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    if (e.dataTransfer?.files) {
      for (const file of e.dataTransfer.files) {
        attachFile(file);
      }
    }
  }

  function handleDragOver(e: DragEvent) {
    e.preventDefault();
  }

  function formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
</script>

<div
  class="border-t border-border bg-background px-4 pb-4 pt-3"
  ondrop={handleDrop}
  ondragover={handleDragOver}
  role="region"
>
  {#if attachedFiles.length > 0}
    <div class="mb-2 flex flex-wrap gap-1.5">
      {#each attachedFiles as file, i}
        <span
          class="inline-flex items-center gap-1 rounded-md bg-muted px-2 py-1 text-xs text-muted-foreground"
        >
          <Paperclip class="size-3" />
          <span class="max-w-32 truncate">{file.name}</span>
          <span class="text-[10px]">({formatSize(file.size)})</span>
          <button
            class="ml-0.5 rounded hover:text-foreground"
            onclick={() => removeFile(i)}
          >
            <X class="size-3" />
          </button>
        </span>
      {/each}
    </div>
  {/if}

  <div class="flex items-end gap-2">
    <button
      class="flex size-9 shrink-0 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
      onclick={() => fileInput?.click()}
      title={$_("chat.input.attach")}
    >
      <Paperclip class="size-4" />
    </button>

    <textarea
      bind:this={textarea}
      bind:value={input}
      oninput={handleInput}
      onkeydown={handleKeydown}
      placeholder={provider
        ? $_("chat.input.placeholder")
        : $_("chat.input.noProvider")}
      disabled={!provider}
      rows={1}
      class="max-h-40 min-h-9 flex-1 resize-none rounded-lg border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:opacity-50"
    ></textarea>

    {#if streaming}
      <button
        class="flex size-9 shrink-0 items-center justify-center rounded-lg bg-destructive text-destructive-foreground transition-colors hover:bg-destructive/90"
        onclick={stopStreaming}
        title={$_("chat.input.stop")}
      >
        <Square class="size-4" />
      </button>
    {:else}
      <button
        class="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
        onclick={handleSend}
        disabled={!canSend}
        title={$_("chat.input.send")}
      >
        <Send class="size-4" />
      </button>
    {/if}
  </div>

  <input
    bind:this={fileInput}
    type="file"
    multiple
    class="hidden"
    onchange={handleFileSelect}
  />
</div>
