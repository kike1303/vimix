<script lang="ts">
	import { Tooltip as TooltipPrimitive } from "bits-ui";
	import type { ComponentProps } from "svelte";

	let {
		ref = $bindable(null),
		...restProps
	}: ComponentProps<typeof TooltipPrimitive.Trigger> = $props();
</script>

<TooltipPrimitive.Trigger bind:ref {...restProps} />
