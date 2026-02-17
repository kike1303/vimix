<script lang="ts">
  import { page } from "$app/state";
  import { _ } from "svelte-i18n";
  import Wrench from "lucide-svelte/icons/wrench";
  import MessageSquare from "lucide-svelte/icons/message-square";

  const isChat = $derived(page.url.pathname === "/chat");
</script>

<nav class="flex items-center gap-0.5 rounded-lg bg-muted p-0.5">
  <a
    href="/"
    class="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors {!isChat
      ? 'bg-background text-foreground shadow-sm'
      : 'text-muted-foreground hover:text-foreground'}"
    aria-current={!isChat ? "page" : undefined}
  >
    <Wrench class="size-3.5" />
    {$_("nav.tools")}
  </a>
  <a
    href="/chat"
    class="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors {isChat
      ? 'bg-background text-foreground shadow-sm'
      : 'text-muted-foreground hover:text-foreground'}"
    aria-current={isChat ? "page" : undefined}
  >
    <MessageSquare class="size-3.5" />
    {$_("nav.chat")}
  </a>
</nav>
