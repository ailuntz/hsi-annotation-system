<script lang="ts">
import { cn } from '$lib/utils/cn';
import type { Snippet } from 'svelte';

interface Props {
	class?: string;
	children?: Snippet;
}

const { class: className = '', children }: Props = $props();
</script>

<div class={cn('space-y-2', className)}>
	{#if children}
		{@render children()}
	{/if}
</div>
