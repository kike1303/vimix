<script lang="ts">
  import { _ } from "svelte-i18n";
  import type { ProcessorCategory } from "$lib/processor-categories";

  let {
    categories,
    processorCounts,
    onselect,
  }: {
    categories: ProcessorCategory[];
    processorCounts: Record<string, number>;
    onselect: (categoryId: string) => void;
  } = $props();
</script>

<div class="grid gap-4 sm:grid-cols-2">
  {#each categories as cat (cat.id)}
    {@const Icon = cat.icon}
    {@const count = processorCounts[cat.id] ?? 0}
    <button
      type="button"
      class="group flex flex-col items-start gap-3 rounded-xl border border-border bg-card p-5
        text-left transition hover:border-primary/50 hover:bg-accent"
      onclick={() => onselect(cat.id)}
    >
      <div class="flex items-center gap-3">
        <div class="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary transition group-hover:bg-primary/20">
          <Icon class="size-5" />
        </div>
        <span class="rounded-full bg-muted px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
          {$_("upload.toolCount", { values: { count } })}
        </span>
      </div>
      <div class="flex flex-col gap-1">
        <span class="text-sm font-semibold text-card-foreground">
          {$_(`categories.${cat.id}.label`)}
        </span>
        <span class="text-xs leading-relaxed text-muted-foreground">
          {$_(`categories.${cat.id}.description`)}
        </span>
      </div>
    </button>
  {/each}
</div>
