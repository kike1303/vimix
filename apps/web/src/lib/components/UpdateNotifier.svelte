<script lang="ts">
  import { isTauri } from "$lib/api";
  import { _ } from "svelte-i18n";
  import { Button } from "$lib/components/ui/button";

  type UpdateStatus = "idle" | "available" | "downloading" | "restarting" | "error";

  let status: UpdateStatus = $state("idle");
  let newVersion = $state("");

  async function checkForUpdates() {
    if (!isTauri()) return;

    try {
      const { check } = await import("@tauri-apps/plugin-updater");
      const update = await check();
      if (update) {
        newVersion = update.version;
        status = "available";

        // Store the update object for later use
        updateRef = update;
      }
    } catch {
      // Silently ignore — update check is non-critical
    }
  }

  let updateRef: any = $state(null);

  async function installUpdate() {
    if (!updateRef) return;

    try {
      status = "downloading";
      await updateRef.downloadAndInstall();
      status = "restarting";
      // Tauri restarts the app automatically after install on most platforms
    } catch {
      status = "error";
    }
  }

  function dismiss() {
    status = "idle";
  }

  $effect(() => {
    const timer = setTimeout(checkForUpdates, 3000);
    return () => clearTimeout(timer);
  });
</script>

{#if status !== "idle"}
  <div
    class="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-background/95 backdrop-blur-sm"
  >
    <div class="mx-auto flex max-w-4xl items-center justify-between px-6 py-3">
      {#if status === "available"}
        <p class="text-sm text-foreground">
          {$_("update.available", { values: { version: newVersion } })}
        </p>
        <div class="flex items-center gap-2">
          <Button variant="ghost" size="sm" onclick={dismiss}>
            {$_("update.later")}
          </Button>
          <Button size="sm" onclick={installUpdate}>
            {$_("update.install")}
          </Button>
        </div>
      {:else if status === "downloading"}
        <p class="text-sm text-muted-foreground">
          {$_("update.downloading")}
        </p>
        <div class="h-1.5 w-32 overflow-hidden rounded-full bg-muted">
          <div class="h-full animate-pulse rounded-full bg-primary" style="width: 100%"></div>
        </div>
      {:else if status === "restarting"}
        <p class="text-sm text-muted-foreground">
          {$_("update.restarting")}
        </p>
      {:else if status === "error"}
        <p class="text-sm text-destructive">
          {$_("update.error")}
        </p>
        <Button variant="ghost" size="sm" onclick={dismiss}>
          {$_("update.later")}
        </Button>
      {/if}
    </div>
  </div>
{/if}
