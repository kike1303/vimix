<script lang="ts">
  import type { ChatMessage } from "$lib/ai/types";
  import ChatToolCallCard from "./ChatToolCall.svelte";
  import User from "lucide-svelte/icons/user";
  import Sparkles from "lucide-svelte/icons/sparkles";
  import Paperclip from "lucide-svelte/icons/paperclip";

  let { message }: { message: ChatMessage } = $props();

  const isUser = $derived(message.role === "user");
</script>

<div class="flex gap-3 {isUser ? 'flex-row-reverse' : ''}">
  <div
    class="flex size-7 shrink-0 items-center justify-center rounded-full {isUser
      ? 'bg-primary text-primary-foreground'
      : 'bg-muted text-muted-foreground'}"
  >
    {#if isUser}
      <User class="size-3.5" />
    {:else}
      <Sparkles class="size-3.5" />
    {/if}
  </div>

  <div class="min-w-0 max-w-[85%] space-y-1">
    {#if message.files && message.files.length > 0}
      <div class="flex flex-wrap gap-1.5">
        {#each message.files as file}
          <span
            class="inline-flex items-center gap-1 rounded-md bg-muted px-2 py-0.5 text-[11px] text-muted-foreground"
          >
            <Paperclip class="size-3" />
            {file.name}
          </span>
        {/each}
      </div>
    {/if}

    {#if message.content}
      <div
        class="rounded-2xl px-3.5 py-2 text-sm {isUser
          ? 'bg-primary text-primary-foreground'
          : 'bg-muted text-foreground'}"
      >
        <div class="whitespace-pre-wrap break-words">{message.content}</div>
      </div>
    {/if}

    {#if message.toolCalls && message.toolCalls.length > 0}
      {#each message.toolCalls as tc (tc.id)}
        <ChatToolCallCard toolCall={tc} />
      {/each}
    {/if}
  </div>
</div>
