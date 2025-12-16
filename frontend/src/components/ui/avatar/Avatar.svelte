<script lang="ts">
import { cn } from '$lib/utils/cn';

interface Props {
	src?: string;
	alt?: string;
	fallback?: string;
	class?: string;
}

const {
	src,
	alt = '',
	fallback = '',
	class: className = '',
}: Props = $props();

const initials = $derived(fallback || alt.slice(0, 2).toUpperCase());
</script>

<div
	class={cn(
		'relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full',
		className,
	)}
>
	{#if src}
		<img class="aspect-square h-full w-full" {src} {alt} />
	{:else}
		<div
			class="flex h-full w-full items-center justify-center rounded-full bg-muted text-sm font-medium"
		>
			{initials}
		</div>
	{/if}
</div>
