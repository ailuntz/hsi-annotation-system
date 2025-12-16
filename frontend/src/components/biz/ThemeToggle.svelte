<script lang="ts">
import { Button } from '$components/ui/button';
import { theme } from '$lib/stores/ui';
import { onMount } from 'svelte';

let mounted = false;

onMount(() => {
	theme.initialize();
	mounted = true;
});

function toggleTheme() {
	const current = $theme;
	if (current === 'light') {
		theme.set('dark');
	} else if (current === 'dark') {
		theme.set('system');
	} else {
		theme.set('light');
	}
}
</script>

{#if mounted}
	<Button variant="ghost" size="icon" onclick={toggleTheme} aria-label="Toggle theme">
		{#if $theme === 'light'}
			<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
			</svg>
		{:else if $theme === 'dark'}
			<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
			</svg>
		{:else}
			<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
			</svg>
		{/if}
	</Button>
{/if}
