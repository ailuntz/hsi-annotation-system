<script lang="ts">
import { toasts } from '$lib/stores/ui';
import { cn } from '$lib/utils/cn';

interface Props {
	id: string;
	message: string;
	type?: 'success' | 'error' | 'info' | 'warning';
}

const { id, message, type = 'info' }: Props = $props();

const typeStyles = {
	success: 'bg-green-100 text-green-800 border-green-200',
	error: 'bg-red-100 text-red-800 border-red-200',
	info: 'bg-blue-100 text-blue-800 border-blue-200',
	warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
};

function dismiss() {
	toasts.remove(id);
}
</script>

<div
	class={cn(
		'flex items-center justify-between gap-4 rounded-lg border p-4 shadow-lg',
		typeStyles[type],
	)}
	role="alert"
>
	<p class="text-sm">{message}</p>
	<button
		onclick={dismiss}
		class="text-current opacity-70 hover:opacity-100"
		aria-label="Dismiss"
	>
		<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
		</svg>
	</button>
</div>
