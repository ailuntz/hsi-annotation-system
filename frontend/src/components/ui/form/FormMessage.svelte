<script lang="ts">
import { cn } from '$lib/utils/cn';

interface Props {
	error?: string | string[];
	class?: string;
}

const { error, class: className = '' }: Props = $props();

const errorMessage = $derived(Array.isArray(error) ? error[0] : error);
</script>

{#if errorMessage}
	<p class={cn('text-sm font-medium text-destructive', className)}>
		{errorMessage}
	</p>
{/if}
