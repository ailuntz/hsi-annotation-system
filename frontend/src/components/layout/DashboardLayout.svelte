<script lang="ts">
import DashboardHeader from './DashboardHeader.svelte';
import DashboardSidebar from './DashboardSidebar.svelte';
</script>

<div class="flex min-h-screen">
	<DashboardSidebar />
	<div class="flex flex-1 flex-col">
		<DashboardHeader />
		<main class="flex-1 p-4 lg:p-6">
			<slot />
		</main>
	</div>
</div>
