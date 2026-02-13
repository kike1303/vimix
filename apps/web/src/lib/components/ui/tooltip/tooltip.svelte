<script lang="ts">
	import { Tooltip as TooltipPrimitive } from "bits-ui";
	import type { ComponentProps } from "svelte";

	let {
		delayDuration = 200,
		...restProps
	}: ComponentProps<typeof TooltipPrimitive.Root> = $props();
</script>

<TooltipPrimitive.Root {delayDuration} {...restProps} />
