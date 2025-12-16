<script lang="ts">
import { cn } from '$lib/utils/cn';

interface Props {
	checked?: boolean;
	disabled?: boolean;
	class?: string;
	onclick?: (e: MouseEvent) => void;
}

let {
	checked = $bindable(false),
	disabled = false,
	class: className = '',
	onclick,
}: Props = $props();

function handleClick(e: MouseEvent) {
	if (!disabled) {
		checked = !checked;
	}
	onclick?.(e);
}
</script>

<button
	type="button"
	role="checkbox"
	aria-checked={checked}
	{disabled}
	class={cn(
		'peer h-4 w-4 shrink-0 rounded-sm border border-primary ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
		checked && 'bg-primary text-primary-foreground',
		className,
	)}
	onclick={handleClick}
>
	{#if checked}
		<svg class="h-full w-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
		</svg>
	{/if}
</button>
