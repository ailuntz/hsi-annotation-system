<script lang="ts">
import { cn } from '$lib/utils/cn';
import type { Snippet } from 'svelte';
import { fade } from 'svelte/transition';

interface Props {
	text?: string;
	position?: 'top' | 'bottom' | 'left' | 'right';
	class?: string;
	children?: Snippet;
}

const { text = '', position = 'top', class: className = '', children }: Props = $props();

let show = $state(false);

const positions = {
	top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
	bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
	left: 'right-full top-1/2 -translate-y-1/2 mr-2',
	right: 'left-full top-1/2 -translate-y-1/2 ml-2',
};
</script>

<div
	class="relative inline-block"
	onmouseenter={() => (show = true)}
	onmouseleave={() => (show = false)}
	onfocus={() => (show = true)}
	onblur={() => (show = false)}
	role="tooltip"
>
	{#if children}
		{@render children()}
	{/if}
	{#if show && text}
		<div
			class={cn(
				'absolute z-50 whitespace-nowrap rounded-md bg-popover px-3 py-1.5 text-sm text-popover-foreground shadow-md border',
				positions[position],
				className,
			)}
			transition:fade={{ duration: 100 }}
		>
			{text}
		</div>
	{/if}
</div>
