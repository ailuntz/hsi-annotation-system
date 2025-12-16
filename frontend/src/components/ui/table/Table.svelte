<script lang="ts">
import { cn } from '$lib/utils/cn';
import type { Snippet } from 'svelte';

interface Props {
	class?: string;
	children?: Snippet;
}

const { class: className = '', children }: Props = $props();
</script>

<div class="relative w-full overflow-auto">
	<table class={cn('w-full caption-bottom text-sm', className)}>
		{#if children}
			{@render children()}
		{/if}
	</table>
</div>
