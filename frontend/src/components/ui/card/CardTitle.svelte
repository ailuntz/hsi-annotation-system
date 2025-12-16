<script lang="ts">
import { cn } from '$lib/utils/cn';
import type { Snippet } from 'svelte';
import type { HTMLAttributes } from 'svelte/elements';

interface Props extends HTMLAttributes<HTMLHeadingElement> {
	class?: string;
	children?: Snippet;
}

const { class: className = '', children, ...restProps }: Props = $props();
</script>

<h3 class={cn('text-2xl font-semibold leading-none tracking-tight', className)} {...restProps}>
	{#if children}
		{@render children()}
	{/if}
</h3>
