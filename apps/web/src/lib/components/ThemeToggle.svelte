<script lang="ts">
  import Sun from "lucide-svelte/icons/sun";
  import Moon from "lucide-svelte/icons/moon";
  import { toggleMode } from "mode-watcher";
  import { Button } from "$lib/components/ui/button/index.js";
  import { _ } from "svelte-i18n";
</script>

<Button onclick={toggleMode} variant="ghost" size="icon-sm">
  <Sun class="size-4 scale-100 rotate-0 dark:scale-0" />
  <Moon class="absolute size-4 scale-0 dark:scale-100" />
  <span class="sr-only">{$_("theme.toggle")}</span>
</Button>
