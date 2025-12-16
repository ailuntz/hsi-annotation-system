<script lang="ts">
import { cn } from '$lib/utils/cn';
import { fade, fly } from 'svelte/transition';
import type { Snippet } from 'svelte';

interface Props {
	open?: boolean;
	title?: string;
	side?: 'left' | 'right';
	class?: string;
	onclose?: () => void;
	children?: Snippet;
}

let {
	open = $bindable(false),
	title = '',
	side = 'right',
	class: className = '',
	onclose,
	children
}: Props = $props();

function close() {
	open = false;
	onclose?.();
}

function handleKeydown(e: KeyboardEvent) {
	if (e.key === 'Escape') close();
}

const flyParams = $derived(
	side === 'right' ? { x: 300, duration: 200 } : { x: -300, duration: 200 }
);
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open}
	<div class="fixed inset-0 z-50" role="dialog" aria-modal="true">
		<!-- Backdrop -->
		<button
			class="fixed inset-0 bg-black/50"
			onclick={close}
			aria-label="Close drawer"
			transition:fade={{ duration: 150 }}
		></button>

		<!-- Content -->
		<div
			class={cn(
				'fixed inset-y-0 z-50 flex w-full max-w-sm flex-col border bg-background shadow-lg',
				side === 'right' ? 'right-0 border-l' : 'left-0 border-r',
				className,
			)}
			transition:fly={flyParams}
		>
			{#if title}
				<div class="flex items-center justify-between border-b px-6 py-4">
					<h2 class="text-lg font-semibold">{title}</h2>
					<button
						class="rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
						onclick={close}
						aria-label="Close"
					>
						<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>
			{/if}
			<div class="flex-1 overflow-auto p-6">
				{@render children?.()}
			</div>
		</div>
	</div>
{/if}
