<script lang="ts">
	import { Tooltip as TooltipPrimitive } from "bits-ui";
	import type { ComponentProps } from "svelte";

	let {
		delayDuration = 200,
		...restProps
	}: ComponentProps<typeof TooltipPrimitive.Provider> = $props();
</script>

<TooltipPrimitive.Provider {delayDuration} {...restProps} />
