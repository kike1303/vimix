<script lang="ts">
  import "../app.css";
  import "$lib/i18n";
  import { ModeWatcher } from "mode-watcher";
  import { _, isLoading } from "svelte-i18n";
  import ThemeToggle from "$lib/components/ThemeToggle.svelte";
  import LangToggle from "$lib/components/LangToggle.svelte";

  let { children } = $props();
</script>

<ModeWatcher />

{#if $isLoading}
  <div class="flex min-h-screen items-center justify-center bg-background">
    <p class="text-muted-foreground">Loading...</p>
  </div>
{:else}
  <div class="flex min-h-screen flex-col bg-background text-foreground">
    <header class="border-b border-border">
      <div class="mx-auto flex max-w-4xl items-center justify-between px-6 py-3">
        <a href="/" class="text-lg font-bold tracking-tight">
          <span class="text-primary">Vi</span>mix
        </a>
        <div class="flex items-center gap-1">
          <span class="mr-2 hidden text-xs text-muted-foreground sm:block">
            {$_("app.tagline")}
          </span>
          <LangToggle />
          <ThemeToggle />
        </div>
      </div>
    </header>

    <main class="mx-auto w-full max-w-4xl flex-1 px-6 py-10">
      {@render children()}
    </main>

    <footer class="border-t border-border py-4 text-center text-xs text-muted-foreground">
      Vimix &mdash; {$_("app.tagline")}
    </footer>
  </div>
{/if}
