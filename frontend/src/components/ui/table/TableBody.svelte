<script lang="ts">
import { cn } from '$lib/utils/cn';
import type { Snippet } from 'svelte';

interface Props {
	class?: string;
	children?: Snippet;
}

const { class: className = '', children }: Props = $props();
</script>

<tbody class={cn('[&_tr:last-child]:border-0', className)}>
	{#if children}
		{@render children()}
	{/if}
</tbody>
