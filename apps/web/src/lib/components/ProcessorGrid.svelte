<script lang="ts">
  import type { Processor } from "$lib/api";
  import { _ } from "svelte-i18n";
  import { getProcessorIcon } from "$lib/processor-icons";
  import { toggleFavorite, isFavorite } from "$lib/stores/favorites.svelte";
  import Heart from "lucide-svelte/icons/heart";

  let {
    processors,
    onselect,
  }: {
    processors: Processor[];
    onselect: (proc: Processor) => void;
  } = $props();

  function procLabel(proc: Processor): string {
    const key = `processors.${proc.id}.label`;
    const translated = $_(key);
    return translated !== key ? translated : proc.label;
  }

  function procDescription(proc: Processor): string {
    const key = `processors.${proc.id}.description`;
    const translated = $_(key);
    return translated !== key ? translated : proc.description;
  }
</script>

<div class="grid gap-4 sm:grid-cols-2">
  {#each processors as proc (proc.id)}
    {@const Icon = getProcessorIcon(proc.id)}
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
      class="group relative flex cursor-pointer flex-col items-start gap-3 rounded-xl border border-border bg-card p-5
        text-left transition hover:border-primary/50 hover:bg-accent"
      onclick={() => onselect(proc)}
      onkeydown={(e: KeyboardEvent) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onselect(proc); } }}
      role="button"
      tabindex="0"
    >
      <button
        type="button"
        class="absolute right-3 top-3 rounded-md p-1 transition
          {isFavorite(proc.id)
            ? 'text-red-500 opacity-100'
            : 'text-muted-foreground/40 opacity-0 hover:text-red-400 group-hover:opacity-100'}
          hover:bg-muted/50"
        onclick={(e: MouseEvent) => {
          e.stopPropagation();
          toggleFavorite(proc.id);
        }}
      >
        <Heart class="size-4" fill={isFavorite(proc.id) ? 'currentColor' : 'none'} />
      </button>

      <div class="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary transition group-hover:bg-primary/20">
        <Icon class="size-5" />
      </div>
      <div class="flex flex-col gap-1">
        <span class="text-sm font-semibold text-card-foreground">
          {procLabel(proc)}
        </span>
        <span class="text-xs leading-relaxed text-muted-foreground">
          {procDescription(proc)}
        </span>
      </div>
      <span class="mt-auto text-[10px] font-medium uppercase tracking-wider text-muted-foreground/60">
        {proc.accepted_extensions.join(" · ")}
      </span>
    </div>
  {/each}
</div>
