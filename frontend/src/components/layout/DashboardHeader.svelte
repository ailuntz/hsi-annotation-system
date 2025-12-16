<script lang="ts">
import ThemeToggle from '$components/biz/ThemeToggle.svelte';
import UserMenu from '$components/biz/UserMenu.svelte';
import { sidebarOpen } from '$lib/stores/ui';

function toggleSidebar() {
	sidebarOpen.update((v) => !v);
}
</script>

<header class="sticky top-0 z-40 flex h-14 items-center gap-4 border-b bg-background px-4 lg:px-6">
	<button
		class="lg:hidden inline-flex items-center justify-center rounded-md p-2 text-muted-foreground hover:bg-accent hover:text-accent-foreground"
		onclick={toggleSidebar}
		aria-label="Toggle sidebar"
	>
		<svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
		</svg>
	</button>

	<div class="flex-1"></div>

	<div class="flex items-center gap-4">
		<ThemeToggle />
		<UserMenu />
	</div>
</header>
