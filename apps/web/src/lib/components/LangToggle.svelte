<script lang="ts">
  import { locale } from "svelte-i18n";
  import { Button } from "$lib/components/ui/button/index.js";

  function toggle() {
    locale.set($locale === "es" ? "en" : "es");
  }
</script>

<Button onclick={toggle} variant="ghost" size="icon-sm" class="font-mono text-xs">
  {$locale === "es" ? "EN" : "ES"}
</Button>
