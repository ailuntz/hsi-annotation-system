<script lang="ts">
import { cn } from '$lib/utils/cn';
import type { Snippet } from 'svelte';
import { fade, scale } from 'svelte/transition';

interface Props {
	open?: boolean;
	title?: string;
	class?: string;
	children?: Snippet;
	onclose?: () => void;
}

let {
	open = $bindable(false),
	title = '',
	class: className = '',
	children,
	onclose,
}: Props = $props();

function close() {
	open = false;
	onclose?.();
}

function handleKeydown(e: KeyboardEvent) {
	if (e.key === 'Escape') close();
}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center"
		role="dialog"
		aria-modal="true"
	>
		<!-- Backdrop -->
		<button
			class="fixed inset-0 bg-black/50"
			onclick={close}
			aria-label="Close modal"
			transition:fade={{ duration: 150 }}
		></button>

		<!-- Content -->
		<div
			class={cn(
				'relative z-50 w-full max-w-lg rounded-lg border bg-background p-6 shadow-lg',
				className,
			)}
			transition:scale={{ duration: 150, start: 0.95 }}
		>
			{#if title}
				<div class="mb-4 flex items-center justify-between">
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
			{#if children}
				{@render children()}
			{/if}
		</div>
	</div>
{/if}
