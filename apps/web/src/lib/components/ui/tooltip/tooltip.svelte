<script lang="ts">
	import { Tooltip as TooltipPrimitive } from "bits-ui";
	import type { ComponentProps } from "svelte";

	let {
		openDelay = 200,
		...restProps
	}: ComponentProps<typeof TooltipPrimitive.Root> = $props();
</script>

<TooltipPrimitive.Root {openDelay} {...restProps} />
