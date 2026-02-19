<script lang="ts">
  import { _ } from "svelte-i18n";
  import { connectProviderOAuth, disconnectProvider } from "$lib/stores/ai-providers.svelte";
  import type { ProviderConfig } from "$lib/ai/types";
  import Loader from "lucide-svelte/icons/loader";
  import LogIn from "lucide-svelte/icons/log-in";
  import LogOut from "lucide-svelte/icons/log-out";

  let {
    provider,
    label,
    description,
    disabled = false,
  }: {
    provider?: ProviderConfig;
    label: string;
    description: string;
    disabled?: boolean;
  } = $props();

  let signingIn = $state(false);
  let error = $state<string | null>(null);

  const isConnected = $derived(
    !disabled && provider?.connected && provider?.authType === "oauth",
  );

  async function handleSignIn() {
    if (!provider || disabled) return;
    signingIn = true;
    error = null;
    try {
      const result = await connectProviderOAuth(provider.id);
      if (!result.success) {
        if (result.error === "port_busy") {
          error = $_("settings.oauth.portBusy");
        } else if (result.error === "timeout") {
          error = $_("settings.oauth.timeout");
        } else {
          error = $_("settings.oauth.failed");
        }
      }
    } catch {
      error = $_("settings.oauth.failed");
    } finally {
      signingIn = false;
    }
  }

  function handleSignOut() {
    if (!provider) return;
    disconnectProvider(provider.id);
    error = null;
  }
</script>

{#if disabled}
  <!-- Coming Soon state -->
  <div class="rounded-lg border border-dashed border-border p-3 opacity-60">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <div class="size-2 rounded-full bg-muted-foreground/30"></div>
        <span class="text-sm font-medium">{label}</span>
      </div>
      <span class="rounded-md bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">
        {$_("settings.comingSoon")}
      </span>
    </div>
    <p class="mt-2 text-[10px] text-muted-foreground">{description}</p>
  </div>
{:else if isConnected}
  <!-- Connected state -->
  <div class="rounded-lg border border-primary/50 bg-primary/5 p-3">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <div class="size-2 rounded-full bg-green-500"></div>
        <span class="text-sm font-medium">{label}</span>
      </div>
      <button
        class="inline-flex items-center gap-1 rounded-md bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
        onclick={handleSignOut}
      >
        <LogOut class="size-3" />
        {$_("settings.oauth.signOut")}
      </button>
    </div>
    <p class="mt-2 text-[10px] text-muted-foreground">
      {$_("settings.oauth.connectedVia")}
      {#if provider?.models.length}
        &middot; {$_("settings.modelsAvailable", { values: { count: provider.models.length } })}
      {/if}
    </p>
  </div>
{:else}
  <!-- Disconnected state -->
  <div class="rounded-lg border border-border p-3">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <div class="size-2 rounded-full bg-muted-foreground/30"></div>
        <span class="text-sm font-medium">{label}</span>
      </div>
      <button
        class="inline-flex items-center gap-1.5 rounded-md bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
        onclick={handleSignIn}
        disabled={signingIn}
      >
        {#if signingIn}
          <Loader class="size-3 animate-spin" />
          {$_("settings.oauth.signingIn")}
        {:else}
          <LogIn class="size-3" />
          {$_("settings.oauth.signIn")}
        {/if}
      </button>
    </div>
    <p class="mt-2 text-[10px] text-muted-foreground">{description}</p>
    {#if error}
      <p class="mt-1.5 text-[10px] text-red-500">{error}</p>
    {/if}
  </div>
{/if}
