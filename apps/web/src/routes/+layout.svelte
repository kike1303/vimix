<script lang="ts">
  import "../app.css";
  import "$lib/i18n";
  import { ModeWatcher } from "mode-watcher";
  import { _, isLoading } from "svelte-i18n";
  import { Tooltip } from "bits-ui";
  import { page } from "$app/state";
  import ThemeToggle from "$lib/components/ThemeToggle.svelte";
  import LangToggle from "$lib/components/LangToggle.svelte";
  import NavToggle from "$lib/components/NavToggle.svelte";
  import UpdateNotifier from "$lib/components/UpdateNotifier.svelte";
  import { Toaster } from "$lib/components/ui/sonner/index.js";

  let { children } = $props();

  const isChat = $derived(page.url.pathname.startsWith("/chat"));
</script>

<ModeWatcher />

<Tooltip.Provider>
{#if $isLoading}
  <div class="flex min-h-screen items-center justify-center bg-background">
    <p class="text-muted-foreground">Loading...</p>
  </div>
{:else}
  <div class="flex min-h-screen flex-col bg-background text-foreground">
    <header class="border-b border-border">
      <div class="mx-auto flex max-w-4xl items-center justify-between px-6 py-3">
        <a href="/" class="flex items-center gap-2 text-lg font-bold tracking-tight">
          <img src="/icon.png" alt="Vimix" class="size-7 rounded-md" />
          Vimix
        </a>
        <div class="flex items-center gap-2">
          <span class="mr-1 hidden text-xs text-muted-foreground sm:block">
            {$_("app.tagline")}
          </span>
          <NavToggle />
          <LangToggle />
          <ThemeToggle />
        </div>
      </div>
    </header>

    <main class="w-full flex-1 {isChat ? '' : 'mx-auto max-w-4xl px-6 py-10'}">
      {@render children()}
    </main>

    {#if !isChat}
      <footer class="border-t border-border py-4 text-center text-xs text-muted-foreground">
        Vimix &mdash; {$_("app.tagline")}
      </footer>
    {/if}
  </div>

  <UpdateNotifier />
  <Toaster />
{/if}
</Tooltip.Provider>
