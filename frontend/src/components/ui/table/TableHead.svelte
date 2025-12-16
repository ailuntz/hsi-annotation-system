<script lang="ts">
import { cn } from '$lib/utils/cn';
import type { Snippet } from 'svelte';

interface Props {
	class?: string;
	children?: Snippet;
}

const { class: className = '', children }: Props = $props();
</script>

<th
	class={cn(
		'h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0',
		className,
	)}
>
	{#if children}
		{@render children()}
	{/if}
</th>
