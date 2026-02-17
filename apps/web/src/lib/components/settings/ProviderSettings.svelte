<script lang="ts">
  import { _ } from "svelte-i18n";
  import { providers, detectOllama } from "$lib/stores/ai-providers.svelte";
  import ProviderCard from "./ProviderCard.svelte";
  import OAuthProviderCard from "./OAuthProviderCard.svelte";
  import * as Dialog from "$lib/components/ui/dialog/index.js";
  import Loader from "lucide-svelte/icons/loader";
  import Check from "lucide-svelte/icons/check";
  import X from "lucide-svelte/icons/x";
  import ExternalLink from "lucide-svelte/icons/external-link";

  let { open = $bindable(false) }: { open: boolean } = $props();

  let ollamaStatus: "idle" | "checking" | "found" | "not-found" = $state("idle");

  async function checkOllama() {
    ollamaStatus = "checking";
    const found = await detectOllama();
    ollamaStatus = found ? "found" : "not-found";
  }

  $effect(() => {
    if (open && ollamaStatus === "idle") {
      checkOllama();
    }
  });

  const openaiProvider = $derived(providers.find((p) => p.id === "openai"));
  const openaiConnectedViaOAuth = $derived(
    openaiProvider?.connected && openaiProvider?.authType === "oauth",
  );

  const apiProviders = $derived(
    providers.filter(
      (p) =>
        (p.id === "anthropic" ||
          p.id === "openai" ||
          p.id === "google" ||
          p.id === "openrouter") &&
        !(p.id === "openai" && openaiConnectedViaOAuth),
    ),
  );
  const localProviders = $derived(providers.filter((p) => p.id === "ollama"));
</script>

<Dialog.Root bind:open>
  <Dialog.Content class="max-h-[85vh] overflow-y-auto sm:max-w-lg">
    <Dialog.Header>
      <Dialog.Title>{$_("settings.title")}</Dialog.Title>
      <Dialog.Description>{$_("settings.description")}</Dialog.Description>
    </Dialog.Header>

    <div class="space-y-5 py-2">
      <!-- OAuth Subscriptions -->
      <div>
        <h3 class="mb-2 text-xs font-medium uppercase text-muted-foreground">
          {$_("settings.tier.subscription")}
        </h3>
        <div class="space-y-2">
          <OAuthProviderCard
            provider={openaiProvider}
            label="ChatGPT Plus / Pro"
            description={$_("settings.oauthDescription.chatgpt")}
          />
        </div>
      </div>

      <!-- API Key Providers -->
      <div>
        <h3 class="mb-2 text-xs font-medium uppercase text-muted-foreground">
          {$_("settings.tier.apiKey")}
        </h3>
        <div class="space-y-2">
          {#each apiProviders as provider (provider.id)}
            <ProviderCard {provider} />
          {/each}
        </div>
      </div>

      <!-- Local (Ollama) -->
      <div>
        <div class="mb-2 flex items-center gap-2">
          <h3 class="text-xs font-medium uppercase text-muted-foreground">
            {$_("settings.tier.local")}
          </h3>
          {#if ollamaStatus === "checking"}
            <Loader class="size-3 animate-spin text-muted-foreground" />
          {:else if ollamaStatus === "found"}
            <Check class="size-3 text-green-500" />
          {:else if ollamaStatus === "not-found"}
            <X class="size-3 text-muted-foreground" />
          {/if}
        </div>
        {#each localProviders as provider (provider.id)}
          <ProviderCard {provider} />
        {/each}
        {#if ollamaStatus === "not-found"}
          <p class="mt-1 text-[10px] text-muted-foreground">
            {$_("settings.ollamaNotRunning")}
            <a
              href="https://ollama.com"
              target="_blank"
              rel="noopener"
              class="inline-flex items-center gap-0.5 text-primary hover:underline"
            >
              ollama.com
              <ExternalLink class="size-2" />
            </a>
          </p>
        {/if}
      </div>
    </div>
  </Dialog.Content>
</Dialog.Root>
