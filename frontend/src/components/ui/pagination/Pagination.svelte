<script lang="ts">
import { Button } from '$components/ui/button';
import { cn } from '$lib/utils/cn';

interface Props {
	currentPage?: number;
	totalPages?: number;
	maxVisible?: number;
	class?: string;
	onchange?: (page: number) => void;
}

let {
	currentPage = $bindable(1),
	totalPages = 1,
	maxVisible = 5,
	class: className = '',
	onchange,
}: Props = $props();

function goToPage(page: number) {
	if (page >= 1 && page <= totalPages && page !== currentPage) {
		currentPage = page;
		onchange?.(page);
	}
}

const pages = $derived((() => {
	const items: (number | '...')[] = [];
	if (totalPages <= maxVisible) {
		for (let i = 1; i <= totalPages; i++) items.push(i);
	} else {
		items.push(1);
		const start = Math.max(2, currentPage - 1);
		const end = Math.min(totalPages - 1, currentPage + 1);
		if (start > 2) items.push('...');
		for (let i = start; i <= end; i++) items.push(i);
		if (end < totalPages - 1) items.push('...');
		items.push(totalPages);
	}
	return items;
})());
</script>

<nav class={cn('flex items-center gap-1', className)} aria-label="Pagination">
	<Button
		variant="outline"
		size="icon"
		disabled={currentPage === 1}
		onclick={() => goToPage(currentPage - 1)}
		aria-label="上一页"
	>
		<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
		</svg>
	</Button>

	{#each pages as page}
		{#if page === '...'}
			<span class="px-2 text-muted-foreground">...</span>
		{:else}
			<Button
				variant={page === currentPage ? 'default' : 'outline'}
				size="icon"
				onclick={() => goToPage(page)}
				aria-current={page === currentPage ? 'page' : undefined}
			>
				{page}
			</Button>
		{/if}
	{/each}

	<Button
		variant="outline"
		size="icon"
		disabled={currentPage === totalPages}
		onclick={() => goToPage(currentPage + 1)}
		aria-label="下一页"
	>
		<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
		</svg>
	</Button>
</nav>
