<script lang="ts">
  import type { OptionSchema } from "$lib/api";
  import { _ } from "svelte-i18n";
  import { Slider } from "$lib/components/ui/slider/index.js";
  import * as ToggleGroup from "$lib/components/ui/toggle-group/index.js";
  import * as Card from "$lib/components/ui/card/index.js";
  import * as Tooltip from "$lib/components/ui/tooltip/index.js";
  import Info from "lucide-svelte/icons/info";

  let {
    schema,
    values = $bindable(),
    disabled = false,
  }: {
    schema: OptionSchema[];
    values: Record<string, unknown>;
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
                    value={[Number(values[opt.id] ?? opt.default)]}
                    onValueChange={(v) => (values = { ...values, [opt.id]: v[0] })}
                    {disabled}
                    class="flex-1"
                  />
                  <span class="min-w-10 text-right font-mono text-sm text-foreground">
                    {values[opt.id] ?? opt.default}
                  </span>
                </div>
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
              {/if}
            </div>
          {/if}
        {/each}
      </div>
    </Card.Content>
  </Card.Root>
{/if}
