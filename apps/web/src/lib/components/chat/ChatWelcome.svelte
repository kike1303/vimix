<script lang="ts">
  import { _ } from "svelte-i18n";
  import { getActiveProvider } from "$lib/stores/ai-providers.svelte";
  import Settings from "lucide-svelte/icons/settings";
  import Sparkles from "lucide-svelte/icons/sparkles";

  let { onsend, onopensettings }: { onsend: (text: string) => void; onopensettings: () => void } =
    $props();

  const provider = $derived(getActiveProvider());

  const suggestions = [
    "chat.suggestions.removeBg",
    "chat.suggestions.compressVideo",
    "chat.suggestions.pdfToImage",
    "chat.suggestions.mergepdfs",
  ];
</script>

<div class="flex flex-1 flex-col items-center justify-center gap-6 px-4">
  <div class="flex flex-col items-center gap-3">
    <div
      class="flex size-14 items-center justify-center rounded-2xl bg-primary/10"
    >
      <Sparkles class="size-7 text-primary" />
    </div>
    <h2 class="text-lg font-semibold">{$_("chat.welcome.title")}</h2>
    <p class="max-w-sm text-center text-sm text-muted-foreground">
      {$_("chat.welcome.subtitle")}
    </p>
  </div>

  <div class="flex flex-wrap justify-center gap-2">
    {#each suggestions as key}
      <button
        class="rounded-full border border-border bg-background px-3.5 py-1.5 text-xs text-foreground shadow-sm transition-colors hover:bg-accent"
        onclick={() => onsend($_(key))}
      >
        {$_(key)}
      </button>
    {/each}
  </div>

  {#if !provider}
    <button
      class="mt-2 inline-flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
      onclick={onopensettings}
    >
      <Settings class="size-3.5" />
      {$_("chat.welcome.configure")}
    </button>
  {/if}
</div>
