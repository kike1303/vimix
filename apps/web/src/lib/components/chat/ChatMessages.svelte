<script lang="ts">
  import { messages, isStreaming } from "$lib/stores/chat.svelte";
  import ChatMessageBubble from "./ChatMessage.svelte";
  import Loader from "lucide-svelte/icons/loader";

  let container: HTMLDivElement | undefined = $state();

  const streaming = $derived(isStreaming.current);

  // Auto-scroll on new messages
  $effect(() => {
    // Track changes — access the reactive values
    const _ = messages.length;
    const __ = messages.at(-1)?.content;
    if (container) {
      requestAnimationFrame(() => {
        container!.scrollTop = container!.scrollHeight;
      });
    }
  });
</script>

<div
  bind:this={container}
  class="flex flex-1 flex-col gap-4 overflow-y-auto scroll-smooth px-4 py-4"
>
  {#each messages as message (message.id)}
    <ChatMessageBubble {message} />
  {/each}

  {#if streaming && messages.at(-1)?.content === "" && (!messages.at(-1)?.toolCalls || messages.at(-1)?.toolCalls?.length === 0)}
    <div class="flex gap-3">
      <div class="flex size-7 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
        <Loader class="size-3.5 animate-spin" />
      </div>
    </div>
  {/if}
</div>
