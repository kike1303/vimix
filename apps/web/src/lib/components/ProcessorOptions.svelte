<script lang="ts">
  import type { OptionSchema } from "$lib/api";
  import { _ } from "svelte-i18n";
  import { Slider } from "$lib/components/ui/slider/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import * as ToggleGroup from "$lib/components/ui/toggle-group/index.js";
  import * as Card from "$lib/components/ui/card/index.js";
  import * as Tooltip from "$lib/components/ui/tooltip/index.js";
  import Info from "lucide-svelte/icons/info";

  let {
    schema,
    values = $bindable(),
    sourceWidth = null,
    disabled = false,
  }: {
    schema: OptionSchema[];
    values: Record<string, unknown>;
    sourceWidth?: number | null;
    disabled?: boolean;
  } = $props();

  function optionLabel(id: string, fallback: string): string {
    const key = `options.${id}.label`;
    const translated = $_(key);
    return translated !== key ? translated : fallback;
  }

  function optionDescription(id: string): string | null {
    const key = `options.${id}.description`;
    const translated = $_(key);
    return translated !== key ? translated : null;
  }

  /** Tracks which dimension options are in "custom input" mode. */
  let customDimensions = $state<Set<string>>(new Set());

  function isVisible(opt: OptionSchema): boolean {
    if (!opt.showWhen) return true;
    return Object.entries(opt.showWhen).every(([key, val]) => {
      const current = String(values[key] ?? "");
      if (Array.isArray(val)) return val.includes(current);
      return current === val;
    });
  }
</script>

{#if schema.length > 0}
  <Card.Root>
    <Card.Header>
      <Card.Title class="text-sm">{$_("upload.optionsLabel")}</Card.Title>
    </Card.Header>
    <Card.Content>
      <div class="grid gap-5 sm:grid-cols-2">
        {#each schema as opt (opt.id)}
          {#if isVisible(opt)}
            {@const desc = optionDescription(opt.id)}
            <div class="flex flex-col gap-2">
              <span class="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                {optionLabel(opt.id, opt.label)}
                {#if desc}
                  <Tooltip.Root>
                    <Tooltip.Trigger>
                      <Info class="size-3.5 text-muted-foreground/50 hover:text-muted-foreground transition" />
                    </Tooltip.Trigger>
                    <Tooltip.Content>
                      {desc}
                    </Tooltip.Content>
                  </Tooltip.Root>
                {/if}
              </span>

              {#if opt.type === "number"}
                <div class="flex items-center gap-3">
                  <Slider
                    min={opt.min ?? 1}
                    max={opt.max ?? 100}
                    step={opt.step ?? 1}
                    value={Number(values[opt.id] ?? opt.default)}
                    onValueChange={(v: number) => (values = { ...values, [opt.id]: v })}
                    {disabled}
                    class="flex-1"
                  />
                  <span class="min-w-10 text-right font-mono text-sm text-foreground">
                    {values[opt.id] ?? opt.default}
                  </span>
                </div>
              {:else if opt.type === "text"}
                <Input
                  type="text"
                  value={String(values[opt.id] ?? opt.default ?? "")}
                  oninput={(e) => {
                    const target = e.currentTarget;
                    if (target) values = { ...values, [opt.id]: target.value };
                  }}
                  {disabled}
                  class="h-8 text-sm"
                />
              {:else if opt.type === "select" && opt.choices}
                <ToggleGroup.Root
                  type="single"
                  value={String(values[opt.id] ?? opt.default)}
                  onValueChange={(v) => {
                    if (v) values = { ...values, [opt.id]: v };
                  }}
                  class="flex flex-wrap justify-start gap-1.5"
                  {disabled}
                >
                  {#each opt.choices as choice (choice.value)}
                    <ToggleGroup.Item
                      value={choice.value}
                      class="h-8 px-3 text-xs"
                    >
                      {choice.label}
                    </ToggleGroup.Item>
                  {/each}
                </ToggleGroup.Root>
              {:else if opt.type === "dimension"}
                {@const current = String(values[opt.id] ?? opt.default)}
                {@const isCustom = customDimensions.has(opt.id)}
                {@const filteredPresets = (opt.presets ?? []).filter((p) => sourceWidth == null || p <= sourceWidth)}
                <div class="flex flex-wrap items-center gap-1.5">
                  {#if opt.allow_original}
                    <button
                      type="button"
                      class="h-8 rounded-md border px-3 text-xs font-medium transition
                        {!isCustom && current === 'original'
                        ? 'border-primary bg-primary text-primary-foreground'
                        : 'border-border bg-background text-foreground hover:bg-accent'}"
                      onclick={() => {
                        customDimensions.delete(opt.id);
                        customDimensions = new Set(customDimensions);
                        values = { ...values, [opt.id]: "original" };
                      }}
                      {disabled}
                    >
                      {$_("options.original")}
                    </button>
                  {/if}
                  {#each filteredPresets as preset (preset)}
                    <button
                      type="button"
                      class="h-8 rounded-md border px-3 text-xs font-medium transition
                        {!isCustom && current === String(preset)
                        ? 'border-primary bg-primary text-primary-foreground'
                        : 'border-border bg-background text-foreground hover:bg-accent'}"
                      onclick={() => {
                        customDimensions.delete(opt.id);
                        customDimensions = new Set(customDimensions);
                        values = { ...values, [opt.id]: String(preset) };
                      }}
                      {disabled}
                    >
                      {preset} px
                    </button>
                  {/each}
                  <button
                    type="button"
                    class="h-8 rounded-md border px-3 text-xs font-medium transition
                      {isCustom
                      ? 'border-primary bg-primary text-primary-foreground'
                      : 'border-border bg-background text-foreground hover:bg-accent'}"
                    onclick={() => {
                      if (!isCustom) {
                        customDimensions.add(opt.id);
                        customDimensions = new Set(customDimensions);
                      }
                    }}
                    {disabled}
                  >
                    {$_("options.custom")}
                  </button>
                </div>
                {#if isCustom}
                  <div class="flex items-center gap-2">
                    <Input
                      type="number"
                      min={opt.min ?? 16}
                      max={opt.max ?? 7680}
                      step={1}
                      value={current}
                      oninput={(e) => {
                        const target = e.currentTarget;
                        if (target) values = { ...values, [opt.id]: target.value };
                      }}
                      {disabled}
                      class="h-8 w-24 text-sm"
                    />
                    <span class="text-xs text-muted-foreground">px</span>
                    {#if sourceWidth != null}
                      <span class="text-xs text-muted-foreground">
                        {$_("options.maxSource", { values: { width: sourceWidth } })}
                      </span>
                    {/if}
                  </div>
                {/if}
              {/if}
            </div>
          {/if}
        {/each}
      </div>
    </Card.Content>
  </Card.Root>
{/if}
