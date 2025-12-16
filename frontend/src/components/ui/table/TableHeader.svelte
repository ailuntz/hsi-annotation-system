<script lang="ts">
import { cn } from '$lib/utils/cn';
import type { Snippet } from 'svelte';

interface Props {
	class?: string;
	children?: Snippet;
}

const { class: className = '', children }: Props = $props();
</script>

<thead class={cn('[&_tr]:border-b', className)}>
	{#if children}
		{@render children()}
	{/if}
</thead>
