<script lang="ts">
  import { _ } from "svelte-i18n";
  import {
    updateProvider,
    connectProvider,
    disconnectProvider,
  } from "$lib/stores/ai-providers.svelte";
  import type { ProviderConfig } from "$lib/ai/types";
  import Loader from "lucide-svelte/icons/loader";
  import Check from "lucide-svelte/icons/check";
  import Eye from "lucide-svelte/icons/eye";
  import EyeOff from "lucide-svelte/icons/eye-off";
  import ExternalLink from "lucide-svelte/icons/external-link";

  let { provider }: { provider: ProviderConfig } = $props();

  let showKey = $state(false);
  let connecting = $state(false);

  const needsKey = $derived(provider.id !== "ollama");

  const keyLinks: Record<string, string> = {
    google: "https://aistudio.google.com/app/apikey",
    anthropic: "https://console.anthropic.com/settings/keys",
    openai: "https://platform.openai.com/api-keys",
    openrouter: "https://openrouter.ai/keys",
  };

  async function handleConnect() {
    connecting = true;
    await connectProvider(provider.id);
    connecting = false;
  }

  function handleDisconnect() {
    disconnectProvider(provider.id);
  }
</script>

<div
  class="rounded-lg border border-border p-3 transition-colors {provider.connected
    ? 'border-primary/50 bg-primary/5'
    : ''}"
>
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-2">
      <div
        class="size-2 rounded-full {provider.connected ? 'bg-green-500' : 'bg-muted-foreground/30'}"
      ></div>
      <span class="text-sm font-medium">{provider.name}</span>
    </div>
    {#if provider.connected}
      <button
        class="rounded-md bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
        onclick={handleDisconnect}
      >
        {$_("settings.disconnect")}
      </button>
    {:else}
      <button
        class="rounded-md bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
        onclick={handleConnect}
        disabled={connecting || (needsKey && !provider.apiKey)}
      >
        {#if connecting}
          <Loader class="inline size-3 animate-spin" />
        {:else}
          {$_("settings.connect")}
        {/if}
      </button>
    {/if}
  </div>

  {#if needsKey && !provider.connected}
    <div class="mt-3">
      <div class="flex items-center justify-between">
        <span class="text-xs text-muted-foreground">{$_("settings.apiKey")}</span>
        {#if keyLinks[provider.id]}
          <a
            href={keyLinks[provider.id]}
            target="_blank"
            rel="noopener"
            class="inline-flex items-center gap-1 text-[10px] text-primary hover:underline"
          >
            {$_("settings.getKey")}
            <ExternalLink class="size-2.5" />
          </a>
        {/if}
      </div>
      <div class="relative mt-1">
        <input
          type={showKey ? "text" : "password"}
          value={provider.apiKey}
          oninput={(e) =>
            updateProvider(provider.id, {
              apiKey: (e.target as HTMLInputElement).value,
            })}
          placeholder="Paste your API key"
          class="h-8 w-full rounded-md border border-input bg-background px-2.5 pr-8 text-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        />
        <button
          class="absolute right-1.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          onclick={() => (showKey = !showKey)}
        >
          {#if showKey}
            <EyeOff class="size-3.5" />
          {:else}
            <Eye class="size-3.5" />
          {/if}
        </button>
      </div>
    </div>
  {/if}

  {#if provider.connected}
    <p class="mt-2 text-[10px] text-muted-foreground">
      {$_("settings.modelsAvailable", { values: { count: provider.models.length } })}
    </p>
  {/if}
</div>
