<script lang="ts">
import { cn } from '$lib/utils/cn';
import type { HTMLSelectAttributes } from 'svelte/elements';

interface Props extends HTMLSelectAttributes {
	class?: string;
	options?: { value: string; label: string }[];
	value?: string;
	placeholder?: string;
	allowEmpty?: boolean;
}

let {
	class: className = '',
	options = [],
	value = $bindable(''),
	placeholder = '请选择...',
	allowEmpty = false,
	...restProps
}: Props = $props();
</script>

<select
	class={cn(
		'flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
		className,
	)}
	bind:value
	{...restProps}
>
	{#if placeholder !== null}
		<option value="" disabled={!allowEmpty}>{placeholder}</option>
	{/if}
	{#each options as option}
		<option value={option.value}>{option.label}</option>
	{/each}
</select>
