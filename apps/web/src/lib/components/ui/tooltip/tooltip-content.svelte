<script lang="ts">
	import { Tooltip as TooltipPrimitive } from "bits-ui";
	import { cn } from "$lib/utils.js";
	import type { ComponentProps } from "svelte";

	let {
		ref = $bindable(null),
		sideOffset = 8,
		class: className,
		...restProps
	}: ComponentProps<typeof TooltipPrimitive.Content> = $props();
</script>

<TooltipPrimitive.Portal>
	<TooltipPrimitive.Content
		bind:ref
		data-slot="tooltip-content"
		{sideOffset}
		class={cn(
			"bg-primary text-primary-foreground animate-in fade-in-0 zoom-in-95 z-50 max-w-xs rounded-md px-3 py-1.5 text-xs",
			className,
		)}
		{...restProps}
	/>
</TooltipPrimitive.Portal>
