<script lang="ts">
  import { _ } from "svelte-i18n";
  import { messages, sendMessage, clearChat } from "$lib/stores/chat.svelte";
  import {
    getActiveProvider,
    getAllAvailableModels,
    selectedModel,
    setSelectedModel,
  } from "$lib/stores/ai-providers.svelte";
  import ChatMessages from "./ChatMessages.svelte";
  import ChatInput from "./ChatInput.svelte";
  import ChatWelcome from "./ChatWelcome.svelte";
  import ProviderSettings from "$lib/components/settings/ProviderSettings.svelte";
  import Settings from "lucide-svelte/icons/settings";
  import Plus from "lucide-svelte/icons/plus";
  import ChevronDown from "lucide-svelte/icons/chevron-down";

  let settingsOpen = $state(false);
  const provider = $derived(getActiveProvider());
  const hasMessages = $derived(messages.length > 0);
  const models = $derived(getAllAvailableModels());
  const currentModel = $derived(selectedModel.current);

  function handleSend(text: string) {
    sendMessage(text);
  }

  function handleNewChat() {
    clearChat();
  }

  function handleModelChange(e: Event) {
    const value = (e.target as HTMLSelectElement).value;
    if (!value) return;
    const [providerId, ...rest] = value.split("::");
    const modelId = rest.join("::");
    setSelectedModel({
      providerId: providerId as import("$lib/ai/types").ProviderId,
      modelId,
    });
  }

  function getSelectValue(): string {
    if (!currentModel) return "";
    return `${currentModel.providerId}::${currentModel.modelId}`;
  }
</script>

<div class="flex h-full w-full flex-col">
  <!-- Chat header -->
  <div class="flex items-center justify-between border-b border-border px-4 py-2">
    <div class="flex min-w-0 flex-1 items-center gap-2">
      {#if models.length > 0}
        <div class="relative min-w-0">
          <select
            value={getSelectValue()}
            onchange={handleModelChange}
            class="h-7 min-w-0 max-w-[260px] appearance-none truncate rounded-md border border-input bg-background pl-2 pr-6 text-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          >
            {#each models as model}
              <option value="{model.providerId}::{model.modelId}">
                {model.providerName} / {model.modelId}
              </option>
            {/each}
          </select>
          <ChevronDown
            class="pointer-events-none absolute right-1.5 top-1/2 size-3 -translate-y-1/2 text-muted-foreground"
          />
        </div>
      {:else}
        <span class="text-xs text-muted-foreground">{$_("chat.header.noProvider")}</span>
      {/if}
    </div>
    <div class="flex shrink-0 items-center gap-1">
      {#if hasMessages}
        <button
          class="flex size-7 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          onclick={handleNewChat}
          title={$_("chat.header.newChat")}
        >
          <Plus class="size-3.5" />
        </button>
      {/if}
      <button
        class="flex size-7 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
        onclick={() => (settingsOpen = true)}
        title={$_("chat.header.settings")}
      >
        <Settings class="size-3.5" />
      </button>
    </div>
  </div>

  <!-- Messages or welcome -->
  {#if hasMessages}
    <ChatMessages />
  {:else}
    <ChatWelcome onsend={handleSend} onopensettings={() => (settingsOpen = true)} />
  {/if}

  <!-- Input -->
  <ChatInput onsend={handleSend} />
</div>

<ProviderSettings bind:open={settingsOpen} />
